#!/bin/bash

set -e

python3 -m poetry run pytest tests/fuzz.py $@
