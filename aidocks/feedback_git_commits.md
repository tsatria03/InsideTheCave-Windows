---
name: feedback_git_commits
description: "One commit per fix. Commit only when the dev asks, and push only when they say so; commits pile up locally until then. Never pull/merge/rebase without a go-ahead; force pushes and history rewrites need an explicit go-ahead. Use git commit -F with a message file, and never hide git's errors."
metadata:
  node_type: memory
  type: feedback
---

**Commit only when the dev asks, and push only when the dev asks.** A request to commit is not a request to push (the dev, 2026-10-02: "Only push if I tell you 2. Most of the time I like to make multiple commits before I decide I want to push something."). Let commits pile up locally; push when told, and then everything waiting goes up together. "Commit and push" means both. Don't offer to push after every commit; say how many commits are waiting only when it helps.

**Run the whole test suite every 10 to 20 commits** (the dev, 2026-10-02: "every 10 to 20 commits you make, make sure to re-run all tests found in the tests/case folder."). This is the dev's standing go-ahead for the full suite, which otherwise runs only when asked ([[feedback_dont_run_or_build]]). How to keep count: [[project_safe_test_run]] names the commit the last full run was made on; after each commit, `git rev-list --count <that commit>..HEAD` gives the commits since. Once it reaches 10, run every `tests\case\*.py` (skipping `_*.py`) the safe way, report the result, and record the new commit there; never let it pass 20. A failure is reported at once, not fixed unasked.

**Nothing comes in from elsewhere** (the dev, 2026-10-02: "Expect nothing new to come in if you do a git fetch. I'm going to be the only one working on this project. I'll let you know if that ever changes."). So don't fetch before every push as a routine, and don't report "nothing new came in". A push that is rejected because the remote moved is the one sign something changed: then stop, fetch, and report it.

**Fetching is fine without asking; bringing commits in is not.** Never pull, merge, rebase, cherry-pick or reset onto incoming commits without the dev's go-ahead, each time. When the branch is behind, report the incoming commits and wait.

**Rewriting published history needs an explicit go-ahead every time.** That covers force pushes, amending or rebasing pushed commits, and changing authors. When approved, push with `--force-with-lease=main:<expected hash>`, and keep a local backup branch until the dev is happy.

**Why:** Standing rules the dev carries across their projects. The dev approves what goes into a commit, and after that pushing is routine; history rewrites can lose work, so they stay a deliberate choice.

**How to apply:**
- **Commit without asking for approval of the commands** (the dev, 2026-10-02: "Can you please try to commit things without asking to approve them?"). `git` commands are allowed in `.claude/settings.local.json` for both shells, so run them as plain `git ...` commands: no `cd` in front (the working directory is already the repository), no `cat` heredoc, no pipes into other programs. Write the message with the Write tool, then `git add`, `git commit -F`, `git push origin main` and `git ls-remote origin refs/heads/main`.
- Write the message to a file in the scratchpad and run `git commit -F <file>`. Windows PowerShell 5.1 breaks double quotes inside arguments passed to programs, so `-m` messages with quotes fail. Never send git's error output to `$null`; a failed commit must be visible.
- **One commit per fix or change.** Each commit carries its own todo, changelog, docs and memory lines. When two fixes share a file such as the changelog, stage each fix's lines on their own (build the index blob with `git hash-object -w` and `git update-index --cacheinfo`, since `git add -p` is interactive).
- **Mark the work finished before committing it**, so the finished line goes in the same commit as the work.
- Stage files by name when the commit should hold exactly what the dev approved, or `git add -A` when they ask to commit everything; check `git status` first either way.
- Format: a short summary line, a blank line, then a plain-text description wrapped at about 72 characters, ending with the Claude attribution line. The dev is always the author, and no one else is co-credited ([[feedback_use_github_usernames]], [[project_provenance]]).
- Never commit throwaway working folders. Binary files stay in git history forever even after deletion, so leave them out and say so.
- After pushing, confirm with `git ls-remote origin refs/heads/main` and report the new commit.
- Committing isn't building or running; [[feedback_dont_run_or_build]] still applies to those.
