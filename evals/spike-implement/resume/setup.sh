#!/bin/bash
. "$(dirname "$0")/../project.sh"
git worktree add -q --no-track -b spike/ABC-39/check-whether-invoices-can-be-listed-as-json .claude/worktrees/ABC-39 origin/develop
echo ".claude/worktrees/" >> .git/info/exclude
