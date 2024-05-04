#!/bin/bash

# Run the Python program using python3 with relative path
python3 src/download.py -v -H 127.0.0.1 -p 3006 -d files/download_files -n $1 -w