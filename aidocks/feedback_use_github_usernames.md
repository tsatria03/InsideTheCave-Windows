---
name: feedback_use_github_usernames
description: "Name people by GitHub username, never real names: the dev is tsatria03, the only person working on this port. Applies to commit authors, messages and everything committed."
metadata:
  node_type: memory
  type: feedback
---

Identify people by their GitHub username, never their real name. The dev is **tsatria03**, and this is a solo port ([[project_provenance]]). This applies to:
- commit author and committer names
- commit messages
- everything committed to the repo, including `CLAUDE.md`, `aidocks/`, `README.md` and `docks/`, because all of it is public on GitHub

**Why:** A standing rule the dev carries across their projects.

**How to apply:**
- Check `git config user.name` before committing; it should be `tsatria03`. If it has drifted, pass `--author="tsatria03 <156674543+tsatria03@users.noreply.github.com>"`.
- Emails stay the GitHub noreply address, which links a commit to the right profile.
- Never add `Co-authored-by:` lines for people; the only trailer is Claude's attribution line.
