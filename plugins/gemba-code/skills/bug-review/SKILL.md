---
name: bug-review
description: Reviews a fixed bug from Jira on its own branch. Marks it in Review, proves that its regression test detects the defect and that the fix changes the files of its Root cause, simplifies and reviews the branch against origin/develop, runs its Reproduction and its neighboring inputs again on the final branch, checks each Done when criterion, pushes the branch and registers the time of the phase. It stops, writing nothing, when the bug or its branch is not ready, resumes one already in Review and leaves a drift comment when the test, the fix or a criterion does not hold. Use when the user asks to review a bug or its fix, or gives a bug key whose branch is fixed and ready to be closed. It never merges.
argument-hint: "[bug key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Bug review

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Drift comment template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/drift.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cause-in-test.md`

Until the Review mark this skill only reads: it writes nothing in Jira and nothing in git. It creates or edits no work item: the Root cause and the Done when stay as bug-start declared them. The `site` in `atlassian.json` above is the `cloudId` of every Jira call. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue addCommentToJiraIssue addWorklogToJiraIssue
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the bug.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status`, `description` and `comment`. Its description holds the Root cause, the Neighboring inputs and the Done when; its Evidence comment, the Reproduction and the `ran:` and `read:` lines of the Root cause. Stop, writing nothing and naming it, when:
   - it is not a Bug: say its type;
   - its status is not Implement or Review: say its status.

3. **Check the branch is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --ready bug <KEY> '<Summary>'
   ```

   It refuses when the current branch is not the one of the bug, when the branch has no commits of its own, when files with tracking have uncommitted changes or when the branch is behind `origin/develop`. When it refuses, relay its reason and stop: the bug keeps its status.

4. **Mark it Review,** only when it is in Implement: a bug already in Review is resumed, so skip this step and go on from step 5. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Review: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason and run no more commands.

5. **Prove the regression test fails without the fix.** The first commit of `git log --reverse --format='%H %s' origin/develop..HEAD` is the `test` commit, and the test it adds is the regression test. When its subject does not start with `test(`, leave a drift comment without opening develop. Otherwise run the test on that commit, never in the project itself: its branch, its uncommitted changes and its untracked files stay as they are. Run each of these commands alone and exactly in this form, in this order, with an inner `'` written `'\''`, and close develop also before any stop:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run 'git checkout -q --detach <hash of the test commit> && <command that runs only the regression test>'
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close
   ```

   Run only that test, so a test of the project that already fails cannot stand in for it, and show that it fails with the symptom of the Reproduction, not with an import error or a missing fixture. When it passes or fails for another reason, leave a drift comment.

   When the cause is in the tests, as the reference above defines it, the branch holds only the `test` commit: when it holds another, leave a drift comment, because the product must not change. Otherwise, instead of the `run` above, run the fixed test against the change to the product its Done when names:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run 'git checkout -q --detach <hash of the test commit> && <the change to the product> && git diff --stat && <command that runs only the fixed test>'
   ```

   and show that it fails as the reference above asks. When it passes, the test does not detect the defect: leave a drift comment.

6. **Check the fix touches the cause.** Run `git diff --name-only origin/develop...HEAD` and check that it lists the path of each `read:` line of the Root cause, without its `:<line>`. When a path is missing, leave a drift comment.

7. **Simplify the branch.** Invoke `/simplify origin/develop...HEAD` with the Skill tool, from the bug branch. Commit its fixes in the commit format of the Gemba Code context, split by what was done.

8. **Review the branch.** Invoke `/code-review origin/develop...HEAD` with the Skill tool. Fix each finding and commit it, or report why it stays.

9. **Check each criterion on the final state of the branch.** Run the regression test, the command of the Reproduction, the command each Done when criterion names and the input of each row of Neighboring inputs, and compare each row with its Current behavior. Run only commands that read; when one would write, stop and ask. Report each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met. When a criterion is not met, or a row changes and no Done when criterion asks for that change, leave a drift comment.

10. **Push the branch** with `git push -u origin <branch>`, the current branch, as a command of its own: the person approves it. The first time it creates the branch on the remote; after that it sends the new commits. Say the branch and the commits it sends.

11. **Register the time of the phase.** Read the bug again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Review. Run:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
    ```

    It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the bug with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes; for the regression test the Criterion is the Reproduction, and for a path the fix does not touch, that `read:` line. Then stop until the person decides: do not push and do not register the time.
