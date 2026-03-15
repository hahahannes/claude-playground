#!/usr/bin/env bash
set -e

rsync -avz --update --delete --exclude='data/' --exclude='*.so' session@ngt.cern.ch:/shared/ngt-benchmarks-v2/ data/
