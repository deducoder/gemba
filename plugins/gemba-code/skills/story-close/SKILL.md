---
name: story-close
description: Closes a reviewed story from Jira. Merges its branch into develop with --no-ff, pushes develop, marks the story Done and deletes the branch locally and on the remote. It writes no worklog: each phase already did. It resumes a close whose develop is already pushed. Use when the user asks to close, merge or finish a story, or gives a story key whose review is done and whose branch is pushed.
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

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype` and `status`. Stop, writing nothing and naming it, when:
   - it is not a Story: say its type;
   - its status is not Review: say its status.

3. **Merge the branch** with this command, run alone and exactly in this form, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --merge story <KEY> '<Summary>'
   ```

   It updates `develop` with `git pull --ff-only`, merges `origin/<branch>` into it with `--no-ff` and the message `Merge branch '<branch>' into develop`, stays on `develop` and prints the branch. Keep that branch name for step 6. It refuses, touching nothing, when files with tracking have uncommitted changes, `origin/<branch>` does not exist, the local branch has commits `origin/<branch>` lacks (they were not reviewed) or `develop` does not fast-forward; and when the merge has conflicts it aborts it, goes back to the branch it came from and names the files. When it refuses, relay its reason and stop: nothing is pushed or marked.

4. **Push `develop`,** with `git push` as a command of its own: the person approves it. Say the branch and the commits it sends, from `git log --oneline origin/develop..develop`. When it lists none, `develop` is already pushed: do not push, and go on to step 5. When the push fails or the person declines it, stop: the story is not marked.

5. **Mark it Done.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Done: pick it by destination, never by id. Only once `develop` is on the remote: after the push of step 4, or when step 4 found it already pushed.

   When no transition has Done as its destination, or `transitionJiraIssue` returns an error, stop right there: say so or relay Jira's reason and say that `develop` was already pushed. Do not run step 6: both branches stay as they are.

6. **Delete the branch** once the result of `transitionJiraIssue` shows the story Done, so never alongside that call: first locally with `git branch -d <branch>`, then on the remote with `git push origin --delete <branch>`, the second as a command of its own that the person approves.

7. **Report** the merge commit, the status of the story and the branches deleted. The project is left on `develop`. This skill writes no worklog: `story-implement` and `story-review` already registered the time of their phases.
