---
name: spike-implement
description: Implements a declared spike from Jira by running its experiments in a worktree and publishing the findings in Confluence. Revalidates its Evidence, marks it in Implement, opens its branch from develop in .claude/worktrees without tracking, plans in plan mode against its Done when, runs the experiments committing in the spike branch, publishes the findings as a live doc in Work/Spikes, reports the evidence of each criterion and registers the time of the phase. Use when the user asks to implement, run, research or work on a declared spike, or gives a spike key to start researching. It edits and runs nothing until the plan is approved, never pushes the branch and never merges.
argument-hint: "[spike key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/findings.py *)
---

# Spike implement

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Drift comment template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/drift.md`
```

Findings template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/findings.md`
```

Until the Implement mark this skill only reads, apart from a drift comment, and it creates or edits no work item. The `site` in `atlassian.json` above is the `cloudId` of every Jira and Confluence call, `confluence.space` the space of the findings.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the spike.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `description`, `issuetype`, `status`, `issuelinks`, `parent`, `timetracking` and `comment`. Stop, writing nothing and naming it, when:
   - it is not a Spike: say its type;
   - its status is not Backlog or Implement: say its status;
   - something linked as "is blocked by" is not Done or Cancelled: say which work item;
   - it has an epic (`parent`) that is not in Implement: say the epic and its status. A spike without an epic has nothing to check here.

3. **Revalidate the Done when.** Read the Evidence comment of the spike: re-run each `ran:` command and re-read each `read:` source, and check that they still give what was noted. Run only commands that read; when one would write, stop and ask. When something no longer holds, leave a drift comment and stop, without marking it Implement. A spike already in Implement is resumed, so for it do this step after step 7.

4. **Check the project is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --check spike <KEY> '<Summary>'
   ```

   When it refuses, relay its reason and stop.

5. **Find the folder of the findings.** Read the space of `atlassian.json` above with `getConfluenceSpaces` (its `id` and `homepageId`) and the descendants of its home with `getConfluencePageDescendants`, which lists every depth. The folder is the `Spikes` of type `folder` whose parent is the `Work` of type `folder`. When either is missing, stop, writing nothing and naming which one is missing: the person creates them before the spike starts.

6. **Mark it Implement,** only when it is in Backlog: a spike already in Implement is resumed, so skip this step. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason, create no branch and run no more commands.

7. **Open the worktree** with the same arguments and `--worktree` instead of `--check`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --worktree spike <KEY> '<Summary>'
   ```

   It prints the branch and, on a second line, the folder `.claude/worktrees/<KEY>`, where the branch lives without an upstream. This skill never pushes the branch: the findings live in Confluence.

8. **Plan in plan mode.** The plan names, for each criterion of the Done when of the spike, the experiment that answers it and what each outcome would show. Edit and run nothing until the person approves it; without plan mode, present the plan and wait.

9. **Run the approved experiments inside the worktree,** working in `.claude/worktrees/<KEY>` only (`git -C` for git, the folder as the working directory for everything else), and commit the experimental work in the spike branch in the commit format of the Gemba Code context. Keep each command and its literal output for the findings. Once the experiments are over, stop.

10. **Publish the findings.** Write them with the template above: the title `<KEY> <Summary>` and the first paragraph of the description of the spike as it was read, the Answer, the Evidence with every `ran:` and `read:` of the experiments and the literal output of each, and the Next. Check the draft with this command, run alone and exactly in this form, and fix each problem it names until it passes:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/findings.py --site <site> --key <KEY> <<'FINDINGS'
    <the draft>
    FINDINGS
    ```

    Then create the page with `createConfluencePage`: the `id` of the space as `spaceId`, the `id` of the `Spikes` folder as `parentId`, `subtype: live`, the `title` the script printed and its `body` as ADF (`contentFormat: "adf"`).

11. **Report** each Done when criterion of the spike with its evidence in the form `ran:` or `read:`, the Answer, and the link to the page.

12. **Register the time of the phase.** Read the spike again with `getJiraIssue`, asking only for its `status` and `expand: "changelog"`, and take the time of the last change into Implement. Run:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
    ```

    It prints `timeSpent` and `started`. Propose them to the person as an estimate and wait for the confirmation or for another time. With it, write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment.

## Leave a drift comment

Add it to the spike with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes.
