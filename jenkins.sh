#!/usr/bin/env bash

# Create s3am venv
virtualenv s3am
s3am/bin/pip install s3am==2.0a1.dev93
# Expose binaries to the PATH
mkdir bin
ln -snf ${PWD}/s3am/bin/s3am bin/
export PATH=$PATH:${PWD}/bin

# Create Toil venv
virtualenv venv
. venv/bin/activate
# Adding AWS extra to get boto as required by tests
pip install toil[aws]==3.3.0
make develop
make test
make clean
rm -rf bin s3am
make pypi
rm -rf venv
