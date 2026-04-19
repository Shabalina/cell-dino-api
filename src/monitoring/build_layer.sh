#!/bin/bash
# 1. Clean up
rm -rf python
rm -f deps_layer.zip

# 2. Create the required Lambda structure
mkdir python

# 3. Install for the target platform (Linux x86) using the requirements file
pip install \
    --platform manylinux2014_x86_64 \
    --target=python \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    -r requirements.txt

# 4. Zip the folder so the 'python/' directory is at the root of the zip
zip -r deps_layer.zip python/