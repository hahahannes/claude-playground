#!/usr/bin/env bash
set -e

rsync -avz --update session@ngt.cern.ch:/shared/ngt-benchmarks-v2/ data/
