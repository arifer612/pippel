"""
Script for Pippel to probe Pip for installed packages and modify them.
Instructions and functions are to be executed through pippel.el, a detailed
documentation is provided in it.
"""

import json
import os
import traceback
import sys
import subprocess
from typing import Dict, List, Optional, Tuple

# Parse current Pip version
from pip import __version__ as pip_version

pip_version = tuple(map(int, pip_version.split(".")))
if len(pip_version) == 2:
    pip_version = (*pip_version, 0)


def compare_version(version_a, version_b):
    # type: (tuple, tuple) -> bool
    """
    Compares version tuples.
    Returns True if VERSION_A is greater than or equal to VERSION_B.
    """
    for rank_a, rank_b in zip(version_a, version_b):
        if rank_a != rank_b:
            return rank_a > rank_b
    return True

# Module imports depend on Pip version.
# pylint: disable=import-error, no-name-in-module
from pip._internal.utils.compat import stdlib_pkgs
if compare_version((19, 1, 1), pip_version):
    from pip.commands.install import InstallCommand
    from pip.commands.list import ListCommand
    from pip.commands.show import search_packages_info
    from pip.commands.uninstall import UninstallCommand
    from pip.utils import get_installed_distributions
else:
    from pip._internal.commands.install import InstallCommand
    from pip._internal.commands.list import ListCommand
    from pip._internal.commands.show import search_packages_info
    from pip._internal.commands.uninstall import UninstallCommand

    if compare_version(pip_version, (21, 2, 0)):
        # These are required to get the packages from 21.2
        from pip._internal.metadata import get_environment
        from typing import cast
    if not compare_version(pip_version, (21, 2, 3)):
        # get_installed_distributions is removed from 21.3
        from pip._internal.utils.misc import get_installed_distributions

# pylint: enable=import-error, no-name-in-module


class Server(object):
    """
    Server to communicate between Emacs and Pip.
    """

    def __init__(self, _stdin=None, _stdout=None):
        self.stdin = _stdin if _stdin else sys.stdin
        self.stdout = _stdout if _stdout else sys.stdout

    def write_json(self, result):
        # type: (list) -> None
        """
        Dumps result into STDOUT.
        """
        self.stdout.write(json.dumps(result) + "\n")
        self.stdout.flush()

    def read_json(self):
        # type: () -> Dict[str, str]
        """
        Parses STDIN as a dictionary.
        """
        line = self.stdin.readline()
        if not line:
            raise EOFError()
        return json.loads(line)

    def handle_request(self):
        # type: () -> None
        """
        Sends requests to server.
        """
        request = self.read_json()
        _method = request["method"]
        arg1 = request.get("arg1")
        arg2 = request.get("arg2")
        try:
            self.stdout.write("pip version: %s\n" % str(pip_version))
            self.stdout.write("Executing: %s(%s, %s)\n" %
                              (_method, arg1, arg2))
            method = getattr(self, _method)
            method(arg1, arg2)
            self.stdout.write("Pip finished\n")
        except Exception as exception:
            self.stdout.write("PIPPEL_ERROR <<<\n")
            self.stdout.write("%s\n\n" % exception)
            self.stdout.write("%s\n" % traceback.format_exc())
            self.stdout.write("PIPPEL_ERROR >>>\n")

    def serve_forever(self):
        """
        Keeps server alive until it breaks.
        """
        while True:
            try:
                self.handle_request()
            except (KeyboardInterrupt, EOFError, SystemExit):
                break


class PipBackend(Server):
    """
    Backend server for Pippel with methods.
    """

    @staticmethod
    def in_virtual_env():
        # type: () -> bool
        """
        Returns TRUE if package is run while in a virtual environment.
        """
        if hasattr(sys, "base_prefix"):
            return sys.base_prefix != sys.prefix
        if hasattr(sys, "real_prefix"):
            return sys.real_prefix != sys.prefix
        return False

    def get_installed_packages(self, params="", *args, **kwargs):
        # type: (str, tuple, dict) -> None
        """
        Retrieves all the installed packages in current environment as a dictionary.
        If USER is TRUE and the current python environment is not a virtual environment,
        only the user installed packages are retrieved.
        """
        if compare_version((19, 1, 0), pip_version):
            get_list = ListCommand()
        else:
            get_list = ListCommand("Pippel", "Backend server for the Pippel service.")

        if self.in_virtual_env() or not params:
            params = ""

        options, _ = get_list.parse_args(["--outdated", params])
        skip = set(stdlib_pkgs)

        if compare_version((21, 2, 0), pip_version):
            packages = [
                package
                for package in get_installed_distributions(
                        local_only=options.local,
                        user_only=options.user,
                        editables_only=options.editable,
                        include_editables=options.include_editable,
                        paths=options.path,
                        skip=skip,
                        )
            ]
            final = [
                {
                    "name": attributes.get("name"),
                    "version": attributes.get("version"),
                    "latest": str(getattr(package, "latest_version")),
                    "summary": attributes.get("summary"),
                    "home-page": attributes.get("home-page"),
                }
                for package in get_list.iter_packages_latest_infos(packages, options)
                for attributes in search_packages_info([package.key])
            ]
        else:
            # Pip 21.2 onwards use _ProcessedDists class to contain all the metadata of
            # a package instead of a dictionary.
            packages = [
                cast("_DistWithLatestInfo", d)
                for d in get_environment(options.path).iter_installed_distributions(
                    local_only=options.local,
                    user_only=options.user,
                    editables_only=options.editable,
                    include_editables=options.include_editable,
                    skip=skip,
                )
            ]
            final = [
                {
                    "name": str(getattr(attributes, "name")),
                    "version": str(getattr(attributes, "version")),
                    "latest": str(getattr(package, "latest_version")),
                    "summary": str(getattr(attributes, "summary")),
                    "home-page": str(getattr(attributes, "homepage")),
                }
                for package in get_list.iter_packages_latest_infos(packages, options)
                for attributes in search_packages_info([package.canonical_name])
            ]
        self.write_json(final)

    def install_package(self, _packages, params=None, *args, **kwargs):
        # type: (str, Optional[str]) -> int
        """
        Installs the string of packages and returns the success code.
        """
        if compare_version((19, 1, 0), pip_version):
            install = InstallCommand()
        else:
            install = InstallCommand("Pippel", "Backend server for the Pippel service.")

        assert _packages, "`_packages` should not be an empty string."

        packages = _packages.split()
        if self.in_virtual_env():
            package_args = [sys.executable, "-m", "pip", "install", *packages,
                            "--upgrade"]
            self.stdout.write("Installing %s in a virtual environment\n" %
                              ", ".join(packages))
        elif params:
            package_args = [sys.executable, "-m", "pip", "install", *packages,
                            "--upgrade", "--target", params]
            self.stdout.write("Installing %s to %s\n" %
                              (", ".join(packages), params))
        else:
            package_args = [sys.executable, "-m", "pip", "install", *packages,
                            "--upgrade", "--user"]
            self.stdout.write("Installting %s in the local user space\n" % packages)

        return subprocess.check_call(package_args)

    def remove_package(self, _packages, *args, **kwargs):
        # type: (str, tuple, dict) -> int
        """
        Removes the string of packages and returns the success code.
        """
        if compare_version((19, 1, 0), pip_version):
            uninstall = UninstallCommand()
        else:
            uninstall = UninstallCommand(
                "Pippel", "Backend server for the Pippel service."
            )

        assert _packages, "`packages` should not be an empty string."

        packages = _packages.split()
        package_args = [sys.executable, "-m", "pip", "uninstall", *packages,
                        "--yes"]
        self.stdout.write("Uninstalling %s\n" % ", ".join(packages))

        return subprocess.check_call(package_args)


if __name__ == "__main__":
    stdin = sys.stdin
    stdout = sys.stdout
    with open(os.devnull, "w") as null:
        sys.stdout = sys.stderr = null
    stdout.flush()
    PipBackend(stdin, stdout).serve_forever()
