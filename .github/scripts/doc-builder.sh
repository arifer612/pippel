#!/bin/sh

### doc-builder.sh
### Build README.org using org-babel

emacs -Q --script "$(dirname $(realpath -s $0))/evaluater.el"

