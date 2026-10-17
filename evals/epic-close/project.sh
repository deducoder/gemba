#!/bin/bash
# Builds the project the epic-close cases observe: a git repository declared for Gemba on
# example.atlassian.net. Closing an epic touches no code, so it holds nothing else.
set -e
mkdir -p .gemba/project
cat > .gemba/project/atlassian.json <<'JSON'
{
  "site": "example.atlassian.net",
  "jira": { "project": "ABC" },
  "confluence": { "space": "ABC" }
}
JSON
git init -q
git config user.name eval
git config user.email eval@example.com
git add -A
git commit -qm "initial commit"
