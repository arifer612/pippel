import json
import os
import sys
from typing import Dict, List, Optional

# Parse current Pip version
from pip import __version__ as __pipver
pipver = tuple(map(int, __pipver.split('.')))
if len(pipver) == 2:
    pipver = (*pipver, 0)


def compare_version(version_a, version_b):
    # type: (tuple, tuple) -> bool
    """
    Compares version tuples.
    Returns True if VERSION_A is greater than or equal to VERSION_B.
    """
    for rank_a, rank_b in zip(version_a, version_b):
        if rank_a != rank_b:
            return True if rank_a > rank_b else False
    return True


# Module imports depend on Pip version.
if compare_version((19, 1, 1), pipver):
    from pip.commands.install import InstallCommand
    from pip.commands.list import ListCommand
    from pip.commands.show import search_packages_info
    from pip.commands.uninstall import UninstallCommand
    from pip.utils import get_installed_distributions
else:
    if compare_version((21, 2, 3), pipver):
        # get_installed_distributions is removed from 21.3
        from pip._internal.utils.misc import get_installed_distributions
    from pip._internal.commands.install import InstallCommand
    from pip._internal.commands.list import ListCommand
    from pip._internal.commands.show import search_packages_info
    from pip._internal.commands.uninstall import UninstallCommand


class Server(object):
    def __init__(self, stdin=None, stdout=None):
        if stdin is None:
            self.stdin = sys.stdin
        else:
            self.stdin = stdin
        if stdout is None:
            self.stdout = sys.stdout
        else:
            self.stdout = stdout

    def write_json(self, result):
        self.stdout.write(json.dumps(result) + "\n")
        self.stdout.flush()

    def read_json(self):
        # type: () -> dict
        line = self.stdin.readline()
        if not line:
            raise EOFError()
        return json.loads(line)

    def handle_request(self):
        # type: () -> None
        request = self.read_json()
        method = request["method"]
        params = request["params"]
        packages = request["packages"]
        try:
            method = getattr(self, method, None)
            if not packages:
                result = method()
                self.write_json(result)
            elif not params:
                method(packages)
            else:
                method(packages, params)
            self.stdout.write("Pip finished\n")
        except Exception as e:
            self.stdout.write("%s\n" % e)
            self.stdout.write("Pip error\n")

    def serve_forever(self):
        while True:
            try:
                self.handle_request()
            except (KeyboardInterrupt, EOFError, SystemExit):
                break


class PipBackend(Server):
    @staticmethod
    def in_virtual_env():
        # type: () -> bool
        """
        Returns TRUE if package is run while in a virtual environment.
        """
        if hasattr(sys, "base_prefix"):
            return sys.base_prefix != sys.prefix
        elif hasattr(sys, "real_prefix"):
            return sys.real_prefix != sys.prefix
        else:
            return False

    def get_installed_packages(self):
        # type: () -> List[Dict[str, str]]
        """
        Retrieves all the installed packages in current environment as a dictionary.
        """
        if compare_version((19, 1, 0), pipver):
            get_list = ListCommand()
        else:
            get_list = ListCommand("Pippel",
                                   "Backend server for the Pippel service.")
        options, args = get_list.parse_args(["--outdated"])

        if compare_version((21, 2, 0), pipver):
            packages = [package for package in get_installed_distributions()
                        if package.key != "team"]
            final = [
                {"name": attributes.get("name"),
                "version": attributes.get("version"),
                "latest": str(getattr(package, "latest_version")),
                "summary": attributes.get("summary"),
                "home-page": attributes.get("home-page")
                }
                for package in get_list.iter_packages_latest_infos(packages, options)
                for attributes in search_packages_info([package.key])
            ]
        else:
            # Pip 21.2 onwards use _ProcessedDists class to contain all the metadata of
            # a package instead of a dictionary.
            from pip._internal.utils.compat import stdlib_pkgs
            from pip._internal.metadata import get_environment
            from typing import cast

            skip = set(stdlib_pkgs)
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
                {"name": str(getattr(attributes, "name")),
                "version": str(getattr(attributes, "version")),
                "latest": str(getattr(package, "latest_version")),
                "summary": str(getattr(attributes, "summary")),
                "home-page": str(getattr(attributes, "homepage"))
                }
                for package in get_list.iter_packages_latest_infos(packages, options)
                for attributes in search_packages_info([package.canonical_name])
            ]
        return final

    def install_package(self, packages, params=None):
        # type: (str, Optional[str]) -> int
        """
        Installs the string of packages and returns the success code.
        """
        if compare_version((19, 1, 0), pipver):
            install = InstallCommand()
        else:
            install = InstallCommand("Pippel",
                                     "Backend server for the Pippel service.")

        assert packages , "`packages` should not be an empty string."
        success = 1
        for package in packages.split():
            if self.in_virtual_env():
                args = [package, "--upgrade"]
            elif params:
                args = [package, "--upgrade", "--target", params]
            else:
                args = [package, "--upgrade", "--user"]
            success = install.main(args)
        return success

    def remove_package(self, packages):
        # type: (str) -> int
        """
        Removes the string of packages and returns the success code.
        """
        assert packages , "`packages` should not be an empty string."
        if compare_version((19, 1, 0), pipver):
            uninstall = UninstallCommand()
        else:
            uninstall = UninstallCommand("Pippel",
                                         "Backend server for the Pippel service.")
        success = uninstall.main(packages.split() + ["--yes"])
        return success

if __name__ == "__main__":
    stdin = sys.stdin
    stdout = sys.stdout
    sys.stdout = sys.stderr = open(os.devnull, "w")
    stdout.flush()
    PipBackend(stdin, stdout).serve_forever()
