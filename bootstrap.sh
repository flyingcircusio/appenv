#!/bin/sh
{	# prevent executaion of partial downloads.
set -e

oops() {
    echo "$0:" "$@" >&2
    exit 1
}


t=$(mktemp)
curl -sL https://github.com/flyingcircusio/appenv/raw/master/src/appenv.py -o $t || oops "failed to download appenv"
python3 $t appenv-init
}
