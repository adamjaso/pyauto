#!/bin/bash

set -e

detect_module() {
    name="$1"
    ls "$name/setup.py" > /dev/null 2>&1
    return $?
}

detect_modules() {
    modules=""
    for f in $(ls) ; do
        if detect_module $f ; then
            modules="$modules $f"
        fi
    done
    echo $modules
}

run_module_tests() {
    name="$1"
    echo
    echo "========== $name =========="
    cd $name
    source env3/bin/activate
    if $(ls test.sh > /dev/null 2>&1); then
        ./test.sh
    else
        nose2 -v
    fi
    deactivate
    cd $cwd
}

run_tests() {
    for name in $(detect_modules) ; do
        run_module_tests $name
    done
}

cwd=$(pwd)
modules=$(detect_modules)
run_tests
