"""Unit tests for pippel.py"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))  # noqa: E501,BLK100

from src.pippel import Server, PipBackend  # noqa: E402

server = PipBackend()


def test_list():
    """
    Verifies that the get_installed_packages command works.
    """
    res = server.get_installed_packages("test")
    return 0 if res else 1


def test_install():
    """
    Verifies that the install_package command works.
    """
    return server.install_package("zipp", "test")


def test_remove():
    """
    Verifies that the remove_package command works.
    """
    return server.remove_package("zipp", "test")
