#!/bin/bash
#
# Hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.
# The hook does the following:
#  - install itself into .git/hooks/
#  - update JSON schema  (run tools/generate_json_schema.py)
#  - update unit documentation (run tools/generate_units_documentation.py)
#
# If any error occurs, the commit is stopped

set -e

export BASE_DIR="$(realpath $(dirname $0)/../..)"

# Redirect output to stderr.
exec 1>&2
echo "Execute sylva-core pre-commit hook script"

# install hook
HOOK_PATH="$BASE_DIR/.git/hooks/pre-commit"
RELATIVE_SCRIPT_PATH="$(realpath $0 --relative-to=$(dirname $HOOK_PATH))"
ln -f -s $RELATIVE_SCRIPT_PATH $HOOK_PATH

# Check python requirements
if ! python3 -c 'import yaml'; then
    echo "[ERROR] Python package PyYAML not found"
    echo "PyYAML is mandatory for pre-commit hook script"
    exit 1
fi

# update JSON schema
$BASE_DIR/tools/generate_json_schema.py

# update unit documentation
$BASE_DIR/tools/generate_units_documentation.py

# update CI scenario description
$BASE_DIR/.gitlab/ci/scripts/generate-scenario-description.sh

# update CI tests description
$BASE_DIR/.gitlab/ci/scripts/generate-tests-description.sh

ERRORS=0
if [[ $(git diff $BASE_DIR/charts/sylva-units/values.schema.json) ]]; then
    ERRORS=1
    echo "values.schema.json was updated. Please include it into this commit"
fi
if [[ $(git diff $BASE_DIR/charts/sylva-units/units-description.md) ]]; then
    ERRORS=1
    echo "units-description.md was updated. Please include it into this commit"
fi
if [[ $(git diff $BASE_DIR/.gitlab/README.md) ]]; then
    ERRORS=1
    echo ".gitlab/README.md was updated. Please include it into this commit"
fi
if [[ $(git diff $BASE_DIR/.gitlab/ci/tests/README.md) ]]; then
    ERRORS=1
    echo ".gitlab/ci/tests/README.md was updated. Please include it into this commit"
fi
if [[ $ERRORS == 0 ]]; then
    echo "Pre-commit script succeed"
    exit 0
else
    exit 1
fi
