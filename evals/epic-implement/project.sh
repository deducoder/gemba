#!/bin/bash
# Builds the project the epic-implement cases observe: a repository declared for Gemba on
# example.atlassian.net. The skill reads only Jira, so the project needs no code.
set -e
mkdir -p .gemba/project
cat > .gemba/project/atlassian.json <<'JSON'
{
  "site": "example.atlassian.net",
  "jira": { "project": "ABC" },
  "confluence": { "space": "ABC" }
}
JSON
echo "# Invoices" > README.md
git init -q
git config user.name eval
git config user.email eval@example.com
git add -A
git commit -qm "initial commit"
