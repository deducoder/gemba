---
name: story-implement
description: Implements a declared story from Jira on its own branch. Marks it in Implement, creates its branch from develop, plans in plan mode against its Done when, builds the approved plan, reports the evidence of each criterion and registers the time of the phase. It stops, writing nothing, when the story cannot be built yet, and resumes one already in Implement. Use when the user asks to implement, build or work on a declared story, or gives a story key to start building. It edits no code until the plan is approved, and never merges.
argument-hint: "[story key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
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

Until the Implement mark this skill only reads, and it creates or edits no work item. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status`, `issuelinks`, `parent` and `comment`. Stop, writing nothing and naming it, when:
   - it is not a Story: say its type;
   - its status is not Backlog or Implement: say its status;
   - something linked as "is blocked by" is not Done or Cancelled: say which work item;
   - its epic (`parent`) is not in Implement: say the epic and its status.

3. **Revalidate the Done when.** Read the Evidence comment of the story: re-run each `ran:` command and re-read each `read:` source, and check that they still give what was noted. Run only commands that read; when one would write, stop and ask. When something no longer holds, leave a drift comment and stop.

4. **Check the project is ready** with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --check`. When it refuses, relay its reason and stop: the story keeps its status.

5. **Mark it Implement,** only when it is in Backlog. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase. When Jira refuses, relay its reason and stop: no branch is created.

6. **Create the branch,** or switch to it when it already exists, with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py story <KEY> '<Summary>'
   ```

   It prints the branch. When you marked the story in step 5, push the branch empty with `git push -u origin <branch>`, as a command of its own: the person approves it. A story that was already in Implement is resumed: no mark and no push.

7. **Plan in plan mode.** Read the code the Done when touches before proposing anything. The plan says how each criterion will be shown. Edit nothing until the person approves it; without plan mode, present the plan and wait.

8. **Build the approved plan,** committing on the story branch in the commit format of the Gemba Code context: commits split by what was done and, for code, each failing test committed before the code that makes it pass. When the code contradicts a Done when criterion, leave a drift comment and stop.

9. **Report** each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

10. **Register the time of the phase.** Read the story again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Implement. Run:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
   ```

   It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the story with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above: its headings and labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes. Then stop until the person decides.
