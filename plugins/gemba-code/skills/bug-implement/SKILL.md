---
name: bug-implement
description: Implements a declared bug from Jira on its own branch. Runs its Reproduction on develop without touching the working tree, marks it in Implement, creates its branch from develop, plans in plan mode, commits a failing regression test before the fix, runs its neighboring inputs again before committing the fix, reports the evidence of each criterion and registers the time of the phase. It stops, writing nothing, when the bug cannot be built yet, and resumes one already in Implement. Use when the user asks to fix, implement or work on a declared bug, or gives a bug key to start fixing. It edits no code until the plan is approved, and never merges.
argument-hint: "[bug key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
---

# Bug implement

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Drift comment template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/drift.md`
```

Until the Implement mark this skill only reads, apart from a drift comment, and it creates or edits no work item: the Root cause and the Done when stay as bug-start declared them. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the bug.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `description`, `issuetype`, `status`, `issuelinks` and `comment`. Its description holds the Root cause, the Neighboring inputs and the Done when; its Evidence comment, the Reproduction and the `ran:` and `read:` lines of the Root cause. Stop, writing nothing and naming it, when:
   - it is not a Bug: say its type;
   - its status is not Backlog or Implement: say its status;
   - something linked as "is blocked by" is not Done or Cancelled: say which work item.

3. **Run the Reproduction on develop,** never in the project itself: it may be on another branch, with changes of its own that must stay as they are. Run each of these commands alone and exactly in this form, in this order, with an inner `'` written `'\''`, and close develop also before any stop:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run '<command of the Reproduction>'
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close
   ```

   `open` prints the path of a worktree of develop and `run` runs the command there; keep its literal output. When it no longer shows the failure, stop without marking the bug or creating its branch: show the command and its output.

   Before closing develop, check the Root cause there: run each of its `ran:` commands with `develop.py run` and read each of its `read:` sources in the worktree, and check that they still give what the Evidence noted. When one no longer does, leave a drift comment and stop. Run only commands that read; when one would write, stop and ask.

4. **Check the project is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --check bug <KEY> '<Summary>'
   ```

   Uncommitted changes on the branch of this same bug do not stop it: they are the work to continue. When it refuses, relay its reason and stop.

5. **Mark it Implement,** only when it is in Backlog: a bug already in Implement is resumed, so skip this step and the push of step 6. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason, create no branch and run no more commands.

6. **Create the branch,** or switch to it when it already exists, with the same arguments and without `--check`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py bug <KEY> '<Summary>'
   ```

   It prints the branch. Only if you marked the bug in step 5, push it empty with `git push -u origin <branch>`, as a command of its own: the person approves it.

7. **Plan in plan mode.** Read the code of the `read:` lines of the Root cause before proposing anything. The plan names the regression test that shows the failure of the Reproduction, the fix of the Root cause, and how each Done when criterion will be shown. Edit nothing until the person approves it; without plan mode, present the plan and wait.

8. **Commit the regression test first.** Write a test that fails for the reason the Root cause names, run it and show that failure before committing: it shows the symptom of the Reproduction, not an import error or a missing fixture, and a test that passes or fails for another reason is rewritten, not committed. Then commit it as the first commit of the branch, a `test` commit in the commit format of the Gemba Code context. On a resumed bug whose branch already has that commit, go on to step 9.

9. **Write the fix and run the neighbors.** With the fix in the working tree and before committing it, run the regression test, which now passes, and each row of Neighboring inputs, and compare each row with its Current behavior. When a row changes and no Done when criterion asks for it, stop before committing the fix: name the row, its Current behavior and what it does now.

10. **Commit the fix** apart from the test, as a `fix` commit whose description names the symptom that goes away. When the code contradicts a Done when criterion, leave a drift comment and stop.

11. **Report** each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

12. **Register the time of the phase.** Read the bug again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Implement. Run:

     ```
     python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
     ```

     It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the bug with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes.
