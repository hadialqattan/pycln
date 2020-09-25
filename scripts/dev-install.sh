#!/bin/bash

set -e

function commands {
    echo "======================================================="
    echo ""
    echo "Useful poetry commands:"
    echo ""
    echo "  - Run:"
    echo "      - pycln: [poetry run pycln]"
    echo "      - pytest: [poetry run pytest]"
    echo ""
    echo "  - Add:"
    echo "      - dependency: [poetry add {name}]"
    echo "      - dev-dependency: [poetry add -D {name}]"
    echo ""
    echo "  - Remove:"
    echo "      - dependency: [poetry remove {name}]"
    echo "      - dev-dependency: [poetry remove -D {name}]"
    echo ""
    echo "  - More info:"
    echo "      - help: [poetry -h]"
    echo "      - docs: [https://python-poetry.org/docs/cli/]"
    echo ""
    echo "To show this message again run:"
    echo "  [./scripts/dev-install.sh -h]"
    echo ""
    echo "======================================================="
}

while getopts 'h?' option; do
    case "$option" in
        h|\?) commands
            exit 0
            ;;
    esac
done

# Setup poetry.
python3 -m pip install poetry
poetry install --no-root  # install only the dependencies.

# Setup pre-commit.
python3 -m pip install pre-commit
pre-commit install

# Show the commands.
commands
