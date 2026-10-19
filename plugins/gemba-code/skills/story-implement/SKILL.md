---
name: story-implement
description: Implements a declared story from Jira on its own branch. Marks it in Implement, creates its branch from develop, plans in plan mode against its Done when, builds the approved plan, reports the evidence of each criterion and registers the time of the phase. It stops, writing nothing, when the story cannot be built yet, cancels it with a comment when the person decides so, and resumes one already in Implement. Use when the user asks to implement, build or work on a declared story, or gives a story key to start building. It edits no code until the plan is approved, and never merges.
argument-hint: "[story key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Story implement

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Drift comment template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/drift.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cancelled.md`

Until the Implement mark this skill only reads, apart from a drift comment or a cancellation, and it creates or edits no work item. The `site` in `atlassian.json` above is the `cloudId` of every Jira call. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue addCommentToJiraIssue addWorklogToJiraIssue
```

Each step names the operation it resolved, not the connector tool directly.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status`, `issuelinks`, `parent` and `comment`. Stop, writing nothing and naming it, when:
   - it is not a Story: say its type;
   - its status is not Backlog or Implement: say its status;
   - something linked as "is blocked by" is not Done or Cancelled: say which work item;
   - it has an epic (`parent`) that is not in Implement: say the epic and its status. A story without an epic has nothing to check here.

3. **Revalidate the Done when.** Read the Evidence comment of the story: re-run each `ran:` command and re-read each `read:` source, and check that they still give what was noted. Run only commands that read; when one would write, stop and ask. When something no longer holds, leave a drift comment and stop. A story already in Implement is resumed on its own branch, so for it do this step after step 6.

4. **Check the project is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --check story <KEY> '<Summary>'
   ```

   Uncommitted changes on the branch of this same story do not stop it: they are the work to continue. When it refuses, relay its reason and stop.

5. **Mark it Implement,** only when it is in Backlog: a story already in Implement is resumed, so skip this step. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason, create no branch and run no more commands.

6. **Create the branch,** or switch to it when it already exists, with the same arguments and without `--check`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py story <KEY> '<Summary>'
   ```

   It prints the branch. This skill never pushes it: `story-review` does.

7. **Plan in plan mode.** Read the code the Done when touches before proposing anything. The plan says how each criterion will be shown. Edit nothing until the person approves it; without plan mode, present the plan and wait.

8. **Build the approved plan,** committing on the story branch in the commit format of the Gemba Code context: commits split by what was done and, for code, each failing test committed before the code that makes it pass. When the code contradicts a Done when criterion, leave a drift comment and stop.

9. **Report** each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

10. **Register the time of the phase.** Read the story again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Implement. Run:

     ```
     python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
     ```

     It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the story with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes.

## Cancel the story

When the person decides to cancel the story, in the request or after a stop of this skill, and it is in Backlog or Implement, write the cancellation comment of the template above instead of a drift comment, and check it with this command, run alone and exactly in this form, fixing each problem it names until it passes:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py --site <site> <<'CANCELLED'
<the comment>
CANCELLED
```

Read the transitions with `getTransitionsForJiraIssue`: when none has Cancelled as its destination (`to.name`), say so and stop, writing nothing. Then add what the command printed to the story with `addCommentToJiraIssue` as ADF (`contentFormat: "adf"`), and apply with `transitionJiraIssue` the one whose destination is Cancelled: pick it by destination, never by id. When it returns an error, stop: relay Jira's reason and say that the comment is already on the story. Before the Implement mark, do not mark it Implement and do not create the branch; after it, leave the branch as it is and register the time of the phase as **Register the time of the phase** says. Then stop. A story in any other status is not cancelled here: say its status and stop.
