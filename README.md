Pippel
============

[![Melpa](https://melpa.org/packages/pippel-badge.svg)](http://melpa.org/#/pippel)

This package is an Emacs frontend for the Python package manager pip. As pippel also uses `tabulated-list-mode`, it provides a similiar package menu like `package-list-packages`.

![](https://raw.githubusercontent.com/arifer612/pippel/master/pippel-menu.png)

## Usage

To use it call `M-x pippel-list-packages`.

Shortcuts for `pippel-package-menu-mode` buffers:

 * `m`     `pippel-menu-mark-unmark` remove mark
 * `d`     `pippel-menu-mark-delete` mark for deletion
 * `U`     `pippel-menu-mark-all-upgrades` mark all upgradable
 * `u`     `pippel-menu-mark-upgrade` mark for upgrade
 * `r`     `pippel-list-packages` refresh package list
 * `i`     `pippel-install-package` prompt user for packages
 * `x`     `pippel-menu-execute` perform marked package menu actions
 * `RET`   `pippel-menu-visit-homepage` follow link


## Installation

The package can be installed from MELPA.

    (require 'pippel)

## Changelog
- v1.4 <2021-12-05>
  + Fix for pip >21.1.3 (#c3f10e6)
  + Formmating using black and add docstrings (#0e62405)

- v1.3 <2021-06-15>
  + Fix for pip >19.1.1 (#2480fd3)
  + Maintainer changed to arifer612
