---
name: spike-close
description: Closes a reviewed spike from Jira. Shows the commits of its branch that closing discards, marks the spike Done, deletes its worktree folder and its local branch, and deletes the branch on the remote only when it exists there. A spike is never merged: it merges and pushes nothing, and it writes no comment and no worklog, because the answer is in the findings and each phase already registered its time. It stops, writing nothing, when the spike is not ready or its folder has changes, and it resumes a close that stopped after the Done mark. Use when the user asks to close or finish a spike, or gives a spike key whose review is done ("close the spike…", "cierra el spike…").
argument-hint: "[spike key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
---

# Spike close

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Until the Done mark this skill only reads: it writes nothing in Jira and deletes nothing. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the spike.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype` and `status`. Stop, writing nothing and naming it, when:
   - it is not a Spike: say its type;
   - its status is not Review or Done: say its status.

   A spike already in Done is a close that stopped after the mark: it is resumed, so step 4 does not mark it again.

3. **See what closing discards** with this command, run alone and exactly in this form, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --discard --dry-run spike <KEY> '<Summary>'
   ```

   It deletes nothing. It prints the branch, then `on origin`, `local only` or `gone`, then the commits of the branch that `develop` lacks, one per line. It refuses, touching nothing, when the folder `.claude/worktrees/<KEY>` is not a worktree of the branch, has changes or files without tracking (it lists them) or `origin` cannot be asked: relay its reason and stop, so the spike is not marked and nothing is deleted. Keep the branch and the second line for step 6.

   When the second line is `gone`, neither the folder nor the branch is left anywhere: when the spike is Done, say that there is nothing left to close, change nothing and stop. Otherwise say the branch and the commits before going on, because deleting the branch discards them.

4. **Mark it Done,** only when it is in Review. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Done: pick it by destination, never by id.

   When no transition has Done as its destination, or `transitionJiraIssue` returns an error, stop right there: say so or relay Jira's reason. Do not run steps 5 and 6: the folder and the branch stay as they are.

5. **Delete the folder and the local branch** once the spike is Done (the result of `transitionJiraIssue` shows it, never alongside that call), with the same command without `--dry-run`, run alone: the person approves it.

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --discard spike <KEY> '<Summary>'
   ```

   When the person declines it or it fails, stop: the spike stays Done and the folder and the branch stay. Say so, and do not run step 6.

6. **Delete the branch on the remote** only when step 3 said `on origin`, with `git push origin --delete <branch>` as a command of its own that the person approves. When it said `local only`, touch no remote.

7. **Report** the status of the spike and what was deleted: the folder, the local branch and, when it ran, the remote branch; or that the close was resumed or that nothing was left. The project stays where it was. This skill merges and pushes nothing and writes no comment and no worklog: the answer is in the findings that Jira shows, and `spike-implement` and `spike-review` already registered the time of their phases.
