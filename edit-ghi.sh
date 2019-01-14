#!/bin/bash
MYDIR=$(readlink -f $(dirname ${BASH_SOURCE[0]}))
. $MYDIR/edit-ghi.venv/bin/activate
$MYDIR/edit-ghi.py $*
