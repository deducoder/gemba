---
name: story-implement
description: Implements a declared story from Jira on its own branch. Marks it in Implement, creates its branch from develop, plans in plan mode against its Done when, builds the approved plan, reports the evidence of each criterion and registers the time of the phase. Use when the user asks to implement, build or work on a declared story, or gives a story key to start building. It edits no code until the plan is approved, and never merges.
argument-hint: "[story key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
---

# Story implement

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

This skill takes a declared story from Backlog to built on its own branch. It never merges and creates or edits no work item. Until the Implement mark, it only reads. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status`, `issuelinks` and `comment`. Go on only for a Story in Backlog with nothing linked as "is blocked by" still open; in any other case say what you found and stop.

3. **Revalidate the Done when.** Read the Evidence comment of the story: re-run each `ran:` command and re-read each `read:` source, and check that they still give what was noted. Run only commands that read; when one would write, stop and ask. When something no longer holds, say which criterion and stop.

4. **Mark it Implement.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

5. **Create the branch** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py story <KEY> '<Summary>'
   ```

   It prints the branch it created. Then push it empty with `git push -u origin <branch>`, as a command of its own: the person approves it.

6. **Plan in plan mode.** Read the code the Done when touches before proposing anything. The plan says how each criterion will be shown. Edit nothing until the person approves it; without plan mode, present the plan and wait.

7. **Build the approved plan,** committing on the story branch in the commit format of the Gemba Code context: commits split by what was done and, for code, each failing test committed before the code that makes it pass.

8. **Report** each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

9. **Register the time of the phase.** Read the story again with `getJiraIssue` and `expand: "changelog"`, and take the time of the change into Implement. Run:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
   ```

   It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.
