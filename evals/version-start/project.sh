#!/bin/bash
# Builds the project the version-start cases observe: a product declared for Gemba on
# example.atlassian.net, in a git repository.
set -e
mkdir -p .gemba/project
cat > .gemba/project/atlassian.json <<'JSON'
{
  "site": "example.atlassian.net",
  "jira": { "project": "ABC" },
  "confluence": { "space": "ABC" }
}
JSON
cat > CLAUDE.md <<'MD'
# Gemba

This project uses Gemba, an agentic development framework for Claude Code built on *genchi genbutsu*: go to the source, observe the facts, then act.

## Language

- Conversation: English. How Claude talks with the person.
- Content: English. The body of what gets written: work items, documents, notes.
- Structure: English. Section headings, labels, table headers, template fields and work item titles.
MD
git init -q
git config user.name eval
git config user.email eval@example.com
git add -A
git commit -qm "initial commit"
