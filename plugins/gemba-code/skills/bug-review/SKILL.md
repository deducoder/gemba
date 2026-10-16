---
name: bug-review
description: Reviews a fixed bug from Jira on its own branch. Marks it in Review, proves that its regression test fails without the fix and that the fix changes the files of its Root cause, simplifies and reviews the branch against origin/develop, runs its Reproduction and its neighboring inputs again on the final branch, checks each Done when criterion, pushes the branch and registers the time of the phase. Use when the user asks to review a bug or its fix, or gives a bug key whose branch is fixed and ready to be closed. It never merges.
argument-hint: "[bug key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
---

# Bug review

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

This skill creates or edits no work item: the Root cause and the Done when stay as bug-start declared them. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the bug.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `description` and `comment`. Its description holds the Root cause, the Neighboring inputs and the Done when; its Evidence comment, the Reproduction and the `ran:` and `read:` lines of the Root cause.

3. **Mark it Review.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Review: pick it by destination, never by id. This is the first write of the phase.

4. **Prove the regression test fails without the fix.** The first commit of `git log --reverse --format='%H %s' origin/develop..HEAD` is the `test` commit, and the test it adds is the regression test. Run it on that commit, never in the project itself: its branch, its uncommitted changes and its untracked files stay as they are. Run each of these commands alone and exactly in this form, in this order, with an inner `'` written `'\''`, and close develop also before any stop:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run 'git checkout -q --detach <hash of the test commit> && <command that runs the regression test>'
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close
   ```

   Show that the test fails with the symptom of the Reproduction, not with an import error or a missing fixture.

5. **Check the fix touches the cause.** Run `git diff --name-only origin/develop...HEAD` and check that it lists the path of each `read:` line of the Root cause.

6. **Simplify the branch.** Invoke `/simplify origin/develop...HEAD` with the Skill tool, from the bug branch. Commit its fixes in the commit format of the Gemba Code context, split by what was done.

7. **Review the branch.** Invoke `/code-review origin/develop...HEAD` with the Skill tool. Fix each finding and commit it, or report why it stays.

8. **Check each criterion on the final state of the branch.** Run the regression test, the command of the Reproduction and the input of each row of Neighboring inputs, and compare each row with its Current behavior. Run only commands that read; when one would write, stop and ask. Report each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

9. **Push the branch** with `git push -u origin <branch>`, the current branch, as a command of its own: the person approves it. The first time it creates the branch on the remote; after that it sends the new commits. Say the branch and the commits it sends.

10. **Register the time of the phase.** Read the bug again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Review. Run:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
    ```

    It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.
