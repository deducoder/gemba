#!/bin/bash
# The reviewed spike ABC-39: its branch in .claude/worktrees/ABC-39 with a commit of its own, not pushed.
. "$(dirname "$0")/../../spike-review/project.sh"
git worktree add -q --no-track -b spike/ABC-39/check-whether-invoices-can-be-listed-as-json .claude/worktrees/ABC-39 origin/develop
echo ".claude/worktrees/" >> .git/info/exclude
git -C .claude/worktrees/ABC-39 commit -q --allow-empty -m "test(probe): print the invoices as JSON"
