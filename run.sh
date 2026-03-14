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

# Create a config that outputs into the log directory
sed "s|output:.*|output: ${LOG_DIR}/bandwidth_plot.png|" config.yml > "$LOG_DIR/config.yml"

# Run plot.py and capture output
echo "Running plot.py..."
conda run -n "$ENV_NAME" python plot.py --config "$LOG_DIR/config.yml" > "$LOG_DIR/stdout.log" 2> "$LOG_DIR/stderr.log"
cat "$LOG_DIR/stdout.log"

# Copy plot to repo root as well
cp "$LOG_DIR/bandwidth_plot.png" bandwidth_plot.png

# Commit and push
echo "Committing and pushing..."
git add -A
git commit -m "Update plot and logs"

# Save the commit ID to the log directory
git rev-parse HEAD > "$LOG_DIR/commit_id.txt"
git add "$LOG_DIR/commit_id.txt"
git commit --amend --no-edit

git push origin master
