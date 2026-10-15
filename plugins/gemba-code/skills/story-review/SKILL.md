---
name: story-review
description: Reviews a built story from Jira on its own branch. Marks it in Review, simplifies and reviews the branch against origin/develop, checks each Done when criterion again against its evidence, pushes the branch and registers the time of the phase. Use when the user asks to review a story, or gives a story key whose branch is built and ready to be closed. It never merges.
argument-hint: "[story key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
---

# Story review

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Until the Review mark this skill only reads: it writes nothing in Jira and nothing in git. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status` and `comment`.

3. **Mark it Review.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Review: pick it by destination, never by id. This is the first write of the phase.

4. **Simplify the branch.** Invoke `/simplify origin/develop...HEAD` with the Skill tool, from the story branch. Commit its fixes in the commit format of the Gemba Code context, split by what was done.

5. **Review the branch.** Invoke `/code-review origin/develop...HEAD` with the Skill tool. Fix each finding and commit it, or report why it stays.

6. **Check each criterion on the final state of the branch.** Read the Evidence comment of the story: re-run each `ran:` command and re-read each `read:` source. Run only commands that read; when one would write, stop and ask. Report each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met.

7. **Push the branch,** with `git push` as a command of its own: the person approves it. Say the branch and the commits it sends.

8. **Register the time of the phase.** Read the story again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Review. Run:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
   ```

   It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.
