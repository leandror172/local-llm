---
name: block-bulk-git-add
enabled: true
event: bash
pattern: (?:^|[\n;&|({])\s*(?:rtk\s+)?git\s+add\s+(?:-A\b|--all\b|\.(?:\s|$))
action: block
---

🛑 **Bulk `git add` blocked**

`git add -A` / `git add .` / `git add --all` stages **unrelated pre-existing
untracked files** (scratch dirs, other features' WIP) into the commit.

**Instead:**
- Stage explicit paths — `git add path/a path/b`
- Or stage only tracked-file modifications — `git add -u` (never grabs new untracked files)
