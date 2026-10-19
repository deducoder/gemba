---
name: bug-implement
description: Implements a declared bug from Jira on its own branch. Runs its Reproduction on develop without touching the working tree, marks it in Implement, creates its branch from develop, plans in plan mode, commits a failing regression test before the fix, runs its neighboring inputs again before committing the fix, reports the evidence of each criterion and registers the time of the phase. It stops, writing nothing but a drift comment, when the bug cannot be built yet, cancels it with a comment when the person decides so, and resumes one already in Implement. Use when the user asks to fix, implement or work on a declared bug, or gives a bug key to start fixing. It edits no code until the plan is approved, and never merges.
argument-hint: "[bug key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
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

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cancelled.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cause-in-test.md`

Until the Implement mark this skill only reads, apart from a drift comment or a cancellation, and it creates or edits no work item: the Root cause and the Done when stay as bug-start declared them. The `site` in `atlassian.json` above is the `cloudId` of every Jira call. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue addCommentToJiraIssue addWorklogToJiraIssue
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

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

5. **Mark it Implement,** only when it is in Backlog: a bug already in Implement is resumed, so skip this step. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason, create no branch and run no more commands.

6. **Create the branch,** or switch to it when it already exists, with the same arguments and without `--check`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py bug <KEY> '<Summary>'
   ```

   It prints the branch. This skill never pushes it.

7. **Plan in plan mode.** Read the code of the `read:` lines of the Root cause before proposing anything. The plan names the regression test that shows the failure of the Reproduction, the fix of the Root cause, and how each Done when criterion will be shown. When the cause is in the tests, as the reference above defines it, the plan names the fixed test and the change to the product its Done when says it detects, and no fix of the product. Edit nothing until the person approves it; without plan mode, present the plan and wait.

8. **Commit the regression test first.** Write a test that fails for the reason the Root cause names, run it and show that failure before committing: it shows the symptom of the Reproduction, not an import error or a missing fixture, and a test that passes or fails for another reason is rewritten, not committed. Then commit it as the first commit of the branch, a `test` commit in the commit format of the Gemba Code context. A resumed bug does not repeat what its branch already holds: with that commit, go on to step 9, or to step 11 when the cause is in the tests; with the `fix` commit too, go on to step 11.

   When the cause is in the tests, show instead that the fixed test detects the change to the product its Done when names. Before committing it, open develop as in step 3 and run, alone, with an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run 'cp <project root>/<path of each file of the fixed test> <its path> && <the change to the product> && git diff --stat && <command that runs only the fixed test>'
   ```

   Show that it fails as the reference above asks, then close develop; a test that passes there is rewritten, not committed. Run the fixed test in the project, where it passes, and each row of Neighboring inputs, and compare each row with its Current behavior. Commit the test as the only commit of the branch, a `test` commit, and go on to step 11.

9. **Write the fix and run the neighbors.** With the fix in the working tree and before committing it, run the regression test, which now passes, and each row of Neighboring inputs, and compare each row with its Current behavior. When a row changes and no Done when criterion asks for it, name the row, its Current behavior and what it does now, and find why before committing the fix:
   - **The cause of the bug:** the row's Current behavior comes from the defect the Root cause names, so it belonged in Done when. Leave a drift comment on the Neighboring inputs criterion, with that row as what was found, and stop.
   - **Another cause:** the fix itself changes the row. Rewrite the fix and repeat this step until each row keeps its Current behavior. When no fix of the Root cause keeps it, stop.

10. **Commit the fix** apart from the test, as a `fix` commit whose description names the symptom that goes away. When the code contradicts a Done when criterion, leave a drift comment and stop.

11. **Report** each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

12. **Register the time of the phase.** Read the bug again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Implement. Run:

     ```
     python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
     ```

     It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the bug with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes; for a Root cause line that no longer holds, the Criterion is that `ran:` or `read:` line.

## Cancel the bug

When the person decides to cancel the bug, in the request or after a stop of this skill, and it is in Backlog or Implement, write the cancellation comment of the template above instead of a drift comment, and check it with this command, run alone and exactly in this form, fixing each problem it names until it passes:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py --site <site> <<'CANCELLED'
<the comment>
CANCELLED
```

Read the transitions with `getTransitionsForJiraIssue`: when none has Cancelled as its destination (`to.name`), say so and stop, writing nothing. Then add what the command printed to the bug with `addCommentToJiraIssue` as ADF (`contentFormat: "adf"`), and apply with `transitionJiraIssue` the one whose destination is Cancelled: pick it by destination, never by id. When it returns an error, stop: relay Jira's reason and say that the comment is already on the bug. Before the Implement mark, do not mark it Implement and do not create the branch; after it, leave the branch as it is and register the time of the phase as **Register the time of the phase** says. Then stop. A bug in any other status is not cancelled here: say its status and stop.
