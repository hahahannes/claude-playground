#!/usr/bin/env bash
set -e

ENV_NAME="claude-playground"

# Create conda env if it doesn't exist
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "Creating conda environment '${ENV_NAME}' from environment.yml..."
    conda env create -f environment.yml
else
    echo "Conda environment '${ENV_NAME}' already exists."
fi

# Run plot.py and capture output
echo "Running plot.py..."
conda run -n "$ENV_NAME" python plot.py 2>&1 | tee output.log

# Commit and push
echo "Committing and pushing..."
git add plot.py bandwidth_plot.png output.log environment.yml run.sh
git commit -m "Update plot and logs"
git push origin master
