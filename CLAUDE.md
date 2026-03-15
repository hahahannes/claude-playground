# CLAUDE.md

## Git Workflow

- Always use `git worktree` to work on tasks in parallel, keeping the main worktree clean.
- Create branches using the GitHub CLI (`gh`). Name branches after the issue number (e.g., `issue-42`).
- The active issue number is provided via the `ACTIVE_ISSUE` environment variable. Always read the issue number from this variable rather than asking the user or guessing.
- The issue number is the primary identifier for all branch names, commits, and PR references.

## Pull Requests

- Use `gh pr create` to open a new pull request, or `gh pr edit` to update an existing one.
- Always link the PR to its issue using `Closes #<issue-number>` in the PR body.
- Before creating a PR, check if one already exists for the branch with `gh pr list --head <branch>` and update it instead of creating a duplicate.

## Branch Naming

- Format: `issue-<number>` (e.g., `issue-42`, `issue-137`).
- Never reuse or overwrite branches for different issues.

## Coding

- All steps required to run a program must be captured in a script (e.g., a `setup.sh` or `run.sh`). This includes environment setup, dependency installation, configuration, and execution. Never rely on manual steps that aren't scripted.
- Always include a minimal Dockerfile following best practices (multi-stage builds, minimal base images, non-root user, `.dockerignore`, etc.) to build a container image for the program.
- Always write unit tests for new code. Tests should cover core logic, edge cases, and error handling. Do not consider a task complete until tests are written and passing.

## Output & Reproducibility

- Programs that produce output (data analysis, plots, reports, etc.) must write all results to a dedicated output directory.
- The output directory name must include a datetime stamp (e.g., `output/2026-03-15_143022/`).
- Each output directory must contain:
  - A `metadata.txt` (or similar) file with the git commit hash.
  - The exact command used to run the program.
  - Copies of all configuration files that were used for the run.
