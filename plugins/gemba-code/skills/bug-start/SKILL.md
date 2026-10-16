---
name: bug-start
description: Declares a bug in Jira from a failure. Reproduces it on develop without touching the working tree, names its root cause with evidence, runs the neighboring inputs, drafts the bug and creates it in Backlog with the evidence in a comment. Use when the user reports something that fails or behaves incorrectly in what already exists ("it fails…", "it breaks…", "falla…"), or asks to declare, report or write a bug. Not for a new capability to build. It fixes nothing.
argument-hint: "[failure]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/bug.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/develop.py *)
---

# Bug start

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/bug.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/priority.md`

!`cat ${CLAUDE_SKILL_DIR}/references/estimate.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/out-of-scope.md`

The bug stays in Backlog: this skill changes no status, creates no branch, fixes nothing and creates no work item other than a bug. Everything it runs to observe the failure runs in a worktree of develop, so the branch, the uncommitted changes and the untracked files of the project stay as they were. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

1. **Observe the failure.** Read the code and the history the failure touches, and the commands that already exist to run it (tests, `--help`).

2. **Open develop** with this command, run alone and exactly in this form:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/develop.py open
   ```

   It prints the path of the worktree. Run every command of steps 3 to 5 from that path, never from the project.

3. **Reproduce the failure** with a command, and keep the command and its literal output.

4. **Name the root cause.** Follow the output to the code that produces it, reading only what that trail needs, until you can write it in one sentence: "<mechanism> causes <symptom> because <reason>", in the `Content:` language. A restated symptom is not a cause. Keep each command you ran as a `ran:` line with its output, and each line of code you read as a `read:` line with its path and line.

5. **Run the neighboring inputs:** the inputs near the Reproduction that the code of the `read:` lines also handles and that work correctly today, each with what it does. They are what the fix must not change. An input that fails the same way is part of the failure: it goes in Done when, not in Neighboring inputs.

6. **Close develop** with this command, run alone and exactly in this form:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/develop.py close
   ```

7. **Ask, in one message, only the decisions the failure leaves open and you cannot deduce.** Ask nothing when nothing is missing.

8. **Draft the bug** with the template: its headings, labels, table header and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none.
   - The Reproduction holds the command and the output of step 3, literal; the Root cause of Evidence, the `ran:` and `read:` lines of step 4. They reach Jira as a comment, not in the description.
   - The last Done when criterion says that the behavior of every row of Neighboring inputs does not change.
   - Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. A criterion that restates the request stays plain.
   - Write in Out of scope only what the Out of scope rules above allow. Add `→ <KEY>` only when another work item already covers it.

9. **Give it a priority and an original estimate** with the Bug rules of the priority above and the estimate rules above.

10. **Check the draft** with this command, run alone and exactly in this form, and fix each problem it names until it passes:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/bug.py --site <site> <<'BUG'
    <the draft>
    BUG
    ```

11. **Create the bug** with `createJiraIssue`: the project, the issue type Bug, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), and in `additional_fields` its priority and its estimate as `{"priority": {"name": "<level>"}, "timetracking": {"originalEstimate": "<estimate>"}}`. Then add the `comment` the script printed to the new bug with `addCommentToJiraIssue`, as ADF.

12. **Reply** with the key and link of the bug it created, and nothing else.
