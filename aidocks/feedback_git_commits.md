---
name: feedback_git_commits
description: "One commit per fix. Commit only when the dev asks, then push right away without asking unless they say to hold. Never pull/merge/rebase without a go-ahead; force pushes and history rewrites need an explicit go-ahead. Use git commit -F with a message file, and never hide git's errors."
metadata:
  node_type: memory
  type: feedback
---

**Commit only when the dev asks.** Once a commit is made at their request, **push it to `origin main` straight away**, without asking, **unless the dev has said to hold the pushes**; while that holds, commit when asked and push only when they say so.

**Fetching is fine without asking; bringing commits in is not.** Never pull, merge, rebase, cherry-pick or reset onto incoming commits without the dev's go-ahead, each time. When the branch is behind, report the incoming commits and wait.

**Rewriting published history needs an explicit go-ahead every time.** That covers force pushes, amending or rebasing pushed commits, and changing authors. When approved, push with `--force-with-lease=main:<expected hash>`, and keep a local backup branch until the dev is happy.

**Why:** Standing rules the dev carries across their projects. The dev approves what goes into a commit, and after that pushing is routine; history rewrites can lose work, so they stay a deliberate choice.

**How to apply:**
- Write the message to a file in the scratchpad and run `git commit -F <file>`. Windows PowerShell 5.1 breaks double quotes inside arguments passed to programs, so `-m` messages with quotes fail. Never send git's error output to `$null`; a failed commit must be visible.
- **One commit per fix or change.** Each commit carries its own todo, changelog, docs and memory lines. When two fixes share a file such as the changelog, stage each fix's lines on their own (build the index blob with `git hash-object -w` and `git update-index --cacheinfo`, since `git add -p` is interactive).
- **Mark the work finished before committing it**, so the finished line goes in the same commit as the work.
- Stage files by name when the commit should hold exactly what the dev approved, or `git add -A` when they ask to commit everything; check `git status` first either way.
- Format: a short summary line, a blank line, then a plain-text description wrapped at about 72 characters, ending with the Claude attribution line. The dev is always the author, and no one else is co-credited ([[feedback_use_github_usernames]], [[project_provenance]]).
- Never commit throwaway working folders. Binary files stay in git history forever even after deletion, so leave them out and say so.
- After pushing, confirm with `git ls-remote origin refs/heads/main` and report the new commit.
- Committing isn't building or running; [[feedback_dont_run_or_build]] still applies to those.
