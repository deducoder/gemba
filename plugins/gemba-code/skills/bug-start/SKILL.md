---
name: bug-start
description: Declares a bug in Jira from a failure. Reproduces it on develop without touching the working tree, names its root cause with evidence, runs the neighboring inputs, drafts the bug and creates it in Backlog with the evidence in a comment. Use when the user reports something that fails or behaves incorrectly in what already exists ("it fails…", "it breaks…", "falla…"), or asks to declare, report or write a bug, and may name the work item where it was found. Not for a new capability to build. It fixes nothing.
argument-hint: "[failure]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/bug.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close)
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

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cause-in-test.md`

The bug stays in Backlog: this skill changes no status, creates no branch, fixes nothing and creates no work item other than a bug. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read each work item key the request names** with `getJiraIssue`, all in one batch, before anything else.
   - A key that cannot be read stops the skill: create nothing, and reply with the key and Jira's reason.
   - A Bug the request asks to declare, with no other failure described, stops the skill: create and edit nothing, and reply that it is already declared, with its key and its link.
   - A work item the request names as where the failure was found, a bug or an epic included, is the origin: **Create the bug** links the bug to it. A key named for any other reason is context and gets no link.

3. **Open develop** with this command, run alone and exactly in this form:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py open
   ```

   It prints the path of a worktree of develop. Until **Close develop**, read every file under that path and run every command, alone, in this form, which runs it in the worktree:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py run '<command>'
   ```

   with an inner `'` written `'\''`. Each `run` asks the person's permission like any other command. Never read or run anything in the project itself: it may be on another branch, with changes of its own that must stay as they are. Any stop from here on runs **Close develop** first and creates nothing.

4. **Reproduce the failure.** Read the code and the history the failure touches and the commands that already exist to run it (tests, `--help`), then reproduce it with a command, and keep the command and its literal output. Stop when:
   - what the request asks for does not exist yet in develop, so it is something new to build: reply that it is a story, to declare with `/gemba-code:story-start`;
   - the failure does not happen: show the command and its output.

5. **Name the root cause.** Follow the output to the code that produces it, reading only what that trail needs, until you can write it in one sentence: "<mechanism> causes <symptom> because <reason>", in the `Content:` language. A restated symptom is not a cause. When the cause cannot be named with evidence, for example because the code that produces the output is not in the repository, stop and show what you ran and read. Keep each command you ran as a `ran:` line with its output, and each line of code you read as a `read:` line with its path, relative to the repository, and line. When the cause is in the tests, as the reference above defines it, also find the change to the product the fixed test must detect. In the worktree, fix the test as the Root cause says, make that change and run only the fixed test, to show that it fails as the reference above asks; keep that run as a `ran:` line.

6. **Run the neighboring inputs:** the inputs near the Reproduction that the code of the `read:` lines also handles and that work correctly today, each with what it does. They are what the fix must not change. An input that fails the same way is part of the failure: it goes in Done when, not in Neighboring inputs.

7. **Close develop** with this command, run alone and exactly in this form:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/develop.py close
   ```

8. **Ask, in one message, only the decisions the failure leaves open and you cannot deduce.** Ask nothing when nothing is missing.

9. **Draft the bug** with the template: its headings, labels, table header and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none.
   - The Reproduction holds the command of **Reproduce the failure** as you passed it to `run`, without `develop.py run`, and its output, literal; the Root cause of Evidence, the `ran:` and `read:` lines of **Name the root cause**, with the commands written the same way.
   - When the cause is in the tests, Done when also holds the criterion with that change to the product, in the form the reference above gives.
   - Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. A criterion that restates the request stays plain.
   - Write in Out of scope only what the Out of scope rules above allow. Add `→ <KEY>` only when another work item already covers it.

10. **Give it a priority and an original estimate** with the Bug rules of the priority above and the estimate rules above.

11. **Check the draft** with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/bug.py --site <site> <<'BUG'
   <the draft>
   BUG
   ```

12. **Create the bug** with `createJiraIssue`: the project, the issue type Bug, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), with no parent, and in `additional_fields` its priority and its estimate as `{"priority": {"name": "<level>"}, "timetracking": {"originalEstimate": "<estimate>"}}`. Then add the `comment` the script printed to the new bug with `addCommentToJiraIssue`, as ADF, and link the bug with `createIssueLink`, the link type `Relates`, to each origin of **Read each work item key**.

13. **Reply** with the key and link of the bug it created and the keys it linked it to, and nothing else.
