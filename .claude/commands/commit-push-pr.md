Create a commit, push, and open a pull request for the current changes.

1. Run `git status` and `git diff` to understand all changes
2. Stage relevant files (not outputs/, .env, or credentials)
3. Write a concise commit message based on the actual changes
4. Push to a new branch (name it based on the changes, e.g., `feat/add-pixiv-source` or `fix/arxiv-keyword-filter`)
5. Create a PR with `gh pr create` including a summary and test plan

Ask me to confirm the commit message and branch name before proceeding.
