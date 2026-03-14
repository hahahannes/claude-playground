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

# Copy config to log directory
cp config.yml "$LOG_DIR/config.yml"

# Read number of plot sections from config
NUM_PLOTS=$(conda run -n "$ENV_NAME" python -c "
import yaml
with open('config.yml') as f:
    config = yaml.safe_load(f)
print(len(config['plots']))
")

# Loop over each plot section
for i in $(seq 0 $((NUM_PLOTS - 1))); do
    # Extract plot config fields
    eval "$(conda run -n "$ENV_NAME" python -c "
import yaml, shlex
with open('config.yml') as f:
    config = yaml.safe_load(f)
p = config['plots'][$i]
print(f'SCRIPT={shlex.quote(p[\"script\"])}')
print(f'DATA_DIR={shlex.quote(p[\"data_dir\"])}')
print(f'OUTPUT={shlex.quote(p.get(\"output\", \"plot.png\"))}')
print(f'TITLE={shlex.quote(p.get(\"title\", \"\"))}')
")"

    SCRIPT_NAME=$(basename "$SCRIPT" .py)
    LOG_SUBDIR="$LOG_DIR/$SCRIPT_NAME"
    mkdir -p "$LOG_SUBDIR"

    echo "Running $SCRIPT (data_dir=$DATA_DIR)..."
    conda run -n "$ENV_NAME" python "$SCRIPT" \
        --data-dir "$DATA_DIR" \
        --output "$LOG_SUBDIR/$OUTPUT" \
        --title "$TITLE" \
        > "$LOG_SUBDIR/stdout.log" 2> "$LOG_SUBDIR/stderr.log"
    cat "$LOG_SUBDIR/stdout.log"

    # Copy output plot to repo root
    cp "$LOG_SUBDIR/$OUTPUT" "$OUTPUT"
done

# Commit and push
echo "Committing and pushing..."
git add -A
git commit -m "Update plots and logs"

# Save the commit ID to the log directory
git rev-parse HEAD > "$LOG_DIR/commit_id.txt"
git add "$LOG_DIR/commit_id.txt"
git commit --amend --no-edit

git push origin master
