#!/bin/bash

set -e

# Uninstall poetry.
python3 -m pip uninstall poetry -y

# Uninstall pre-commit (optional).
python3 -m pip uninstall pre-commit
