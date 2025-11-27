#!/bin/bash

# Script to list all unique top-level Python modules imported across
# all .py files in the current directory and its subdirectories.

# Check if the current directory is passed as an argument, otherwise use '.'
SEARCH_DIR=${1:-.}

echo "Scanning for unique Python imports in: $SEARCH_DIR"
echo "----------------------------------------------------"

# 1. find . -name "*.py" : Recursively find all Python files.
# 2. xargs grep -E '^\s*(import|from)\s+' : Pipe the files to grep.
#    -E uses extended regex.
#    '^\s*(import|from)\s+' matches lines starting with optional whitespace,
#    followed by 'import ' or 'from '.
# 3. sed -E 's/^\s*(import|from)[[:space:]]+([^[:space:]\.]+).*$/\2/' :
#    Extracts the root module name.
#    - The module name is the first sequence of characters after 'import' or 'from'
#      that contains neither a space nor a period ('.'). This guarantees that for
#      imports like 'from numpy.fft import fft' or 'import pandas.core', only the
#      top-level name ('numpy' or 'pandas') is captured.
# 4. sort | uniq : Sort the names alphabetically and remove duplicates.
find "$SEARCH_DIR" -type f -name "*.py" -print0 | \
    xargs -0 grep -E '^\s*(import|from)\s+' | \
    sed -E 's/^\s*(import|from)[[:space:]]+([^[:space:]\.]+).*$/\2/' | \
    sort | uniq

echo "----------------------------------------------------"
