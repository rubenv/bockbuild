#!/bin/bash

# Prevents writing .pyc files on Python 2.6 and up.
export PYTHONDONTWRITEBYTECODE=x

exec python $@
