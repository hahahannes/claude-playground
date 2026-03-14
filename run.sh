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

# Create timestamped log directory
LOG_DIR="logs/$(date '+%Y-%m-%d_%H-%M-%S')"
mkdir -p "$LOG_DIR"

# Run plot.py and capture output
echo "Running plot.py..."
conda run -n "$ENV_NAME" python plot.py > "$LOG_DIR/stdout.log" 2> "$LOG_DIR/stderr.log"
cat "$LOG_DIR/stdout.log"

# Commit and push
echo "Committing and pushing..."
git add -A
git commit -m "Update plot and logs"
git push origin master
