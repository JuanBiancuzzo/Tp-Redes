#!/bin/bash

# Run the Python program using python3 with relative path
python3 src/upload.py -v -H 127.0.0.1 -p 3006 -s files/upload_files -n $1 -r