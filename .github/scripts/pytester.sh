#!/bin/bash
# pytester.sh
# 
# Runs PyTest on the unit tests. Takes in 2 parameters.
# example: ./pytester.sh 3.10.1 20.1.1

set -x

PY_VER="$1"
PIP_VER="$2"

if [[ -z ${PY_VER} ]] || [[ -z ${PIP_VER} ]]; then
    exit 127
fi


[[ -d .venv ]] && rm -r .venv
[[ -f Pipfile ]] && rm Pipfile
[[ -f Pipfile.lock ]] && rm Pipfile.lock


mkdir -p .venv/bin
pipenv install --python $PY_VER --no-site-packages pip==$PIP_VER pytest &> /dev/null
pipenv run pytest >> /dev/null
if [[ $? -eq 0 ]]; then
    echo "${PY_VER} ${PIP_VER} [[https://img.shields.io/badge/-PASS-brightgreen.svg]]"
else
    echo "${PY_VER} ${PIP_VER} [[https://img.shields.io/badge/-FAIL-red.svg]]"
fi

exit 0
