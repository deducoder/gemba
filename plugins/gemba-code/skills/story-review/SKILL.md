---
name: story-review
description: Reviews a built story from Jira on its own branch. Marks it in Review, simplifies and reviews the branch against origin/develop, checks each Done when criterion again against its evidence, pushes the branch and registers the time of the phase. It stops, writing nothing, when the story or its branch is not ready, resumes one already in Review and leaves a drift comment when a criterion no longer holds. Use when the user asks to review a story, or gives a story key whose branch is built and ready to be closed. It never merges.
argument-hint: "[story key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Story review

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Drift comment template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/drift.md`
```

Until the Review mark this skill only reads: it writes nothing in Jira and nothing in git. The `site` in `atlassian.json` above is the `cloudId` of every Jira call. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue addCommentToJiraIssue addWorklogToJiraIssue
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the story.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status`, `description` and `comment`. Stop, writing nothing and naming it, when:
   - it is not a Story: say its type;
   - its status is not Implement or Review: say its status.

3. **Check the branch is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --ready story <KEY> '<Summary>'
   ```

   It refuses when the current branch is not the one of the story, when the branch has no commits of its own, when files with tracking have uncommitted changes or when the branch is behind `origin/develop`. When it refuses, relay its reason and stop: the story keeps its status.

4. **Mark it Review,** only when it is in Implement: a story already in Review is resumed, so skip this step and go on from step 5. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Review: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason and do not run `/simplify`.

5. **Simplify the branch.** Invoke `/simplify origin/develop...HEAD` with the Skill tool, from the story branch. Commit its fixes in the commit format of the Gemba Code context, split by what was done.

6. **Review the branch.** Invoke `/code-review origin/develop...HEAD` with the Skill tool. Fix each finding and commit it, or report why it stays.

7. **Check each criterion on the final state of the branch.** Read the Evidence comment of the story: re-run each `ran:` command and re-read each `read:` source. Run only commands that read; when one would write, stop and ask. Report each Done when criterion with its evidence in the form `ran:` or `read:`, naming any that is not met. When something no longer holds, leave a drift comment and stop until the person decides: do not push and do not register the time.

8. **Push the branch** with `git push -u origin <branch>`, the current branch, as a command of its own. The first time it creates the branch on the remote; after that it sends the new commits. Say the branch and the commits it sends.

9. **Register the time of the phase.** Read the story again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Review. Run:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
   ```

   It prints `timeSpent` and `started`. Write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the story with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes.
