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

# Read plot section names and script counts from config
PLOT_ENTRIES=$(conda run -n "$ENV_NAME" python -c "
import yaml
with open('config.yml') as f:
    config = yaml.safe_load(f)
for name, section in config['plots'].items():
    print(f'{name} {len(section[\"scripts\"])}')
")

# Loop over each plot section
echo "$PLOT_ENTRIES" | while read NAME NUM_SCRIPTS; do
    DATA_DIR="data/$NAME"
    LOG_SUBDIR="$LOG_DIR/$NAME"
    mkdir -p "$LOG_SUBDIR"

    for j in $(seq 0 $((NUM_SCRIPTS - 1))); do
        # Extract script config fields
        eval "$(conda run -n "$ENV_NAME" python -c "
import yaml, shlex
with open('config.yml') as f:
    config = yaml.safe_load(f)
s = config['plots']['$NAME']['scripts'][$j]
print(f'SCRIPT={shlex.quote(s[\"script\"])}')
print(f'OUTPUT={shlex.quote(s.get(\"output\", \"plot.png\"))}')
print(f'TITLE={shlex.quote(s.get(\"title\", \"\"))}')
")"

        echo "Running $SCRIPT (data_dir=$DATA_DIR)..."
        conda run -n "$ENV_NAME" python "$SCRIPT" \
            --data-dir "$DATA_DIR" \
            --output "$LOG_SUBDIR/$OUTPUT" \
            --title "$TITLE" \
            > "$LOG_SUBDIR/${SCRIPT%.py}_stdout.log" 2> "$LOG_SUBDIR/${SCRIPT%.py}_stderr.log"
        cat "$LOG_SUBDIR/${SCRIPT%.py}_stdout.log"

        # Copy output plot to repo root
        cp "$LOG_SUBDIR/$OUTPUT" "$OUTPUT"
    done
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
