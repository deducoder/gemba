---
name: story-close
description: Closes a reviewed story from Jira. Merges its branch into develop with --no-ff, pushes develop, marks the story Done and deletes the branch locally and on the remote. It writes no worklog: each phase already did. Use when the user asks to close, merge or finish a story, or gives a story key whose review is done and whose branch is pushed.
argument-hint: "[story key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
---

# Story close

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Until the push this skill only reads and merges locally: it writes nothing in Jira and sends nothing to the remote. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype` and `status`.

3. **Merge the branch** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --merge story <KEY> '<Summary>'
   ```

   It updates `develop` with `git pull --ff-only`, merges `origin/<branch>` into it with `--no-ff` and the message `Merge branch '<branch>' into develop`, stays on `develop` and prints the branch. Keep that branch name for step 6. When it refuses, relay its reason and stop.

4. **Push `develop`,** with `git push` as a command of its own: the person approves it. Say the branch and the commits it sends.

5. **Mark it Done.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Done: pick it by destination, never by id. Only after the push of step 4.

6. **Delete the branch,** once the story is marked: first locally with `git branch -d <branch>`, then on the remote with `git push origin --delete <branch>`, the second as a command of its own that the person approves.

7. **Report** the merge commit, the status of the story and the branches deleted. The project is left on `develop`. This skill writes no worklog: `story-implement` and `story-review` already registered the time of their phases.
