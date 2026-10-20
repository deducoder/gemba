---
name: spike-implement
description: Implements a declared spike from Jira by running its experiments in a worktree and publishing the findings in Confluence. Revalidates its Evidence, marks it in Implement, opens its branch from develop in .claude/worktrees without tracking, plans in plan mode against its Done when, runs the experiments committing in the spike branch, publishes the findings as a live doc in Work/Spikes, reports the evidence of each criterion and registers the time of the phase. Use when the user asks to implement, run, research or work on a declared spike, or to resume one ("implement the spike…", "implementa el spike…", "corre el spike…", "retoma el spike…"), or gives a spike key to start researching. It stops without writing when the spike is not ready, and cancels it with a comment when the person decides so. It edits and runs nothing until the plan is approved, never pushes the branch and never merges.
argument-hint: "[spike key]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/findings.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
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

!`cat ${CLAUDE_PLUGIN_ROOT}/references/cancelled.md`

Findings template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/findings.md`
```

Until the Implement mark this skill only reads, apart from a drift comment or a cancellation, and it creates or edits no work item. The `site` in `atlassian.json` above is the `cloudId` of every Jira and Confluence call, `confluence.space` the space of the findings. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue addCommentToJiraIssue addWorklogToJiraIssue updateConfluencePage createConfluencePage getConfluencePageDescendants getConfluenceSpaces
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the spike.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `description`, `issuetype`, `status`, `issuelinks`, `parent`, `timetracking` and `comment`. Stop, writing nothing and naming it, when:
   - it is not a Spike: say its type;
   - its status is not Backlog or Implement: say its status;
   - something linked as "is blocked by" is not Done or Cancelled: say which work item;
   - it has an epic (`parent`) that is not in Implement: say the epic and its status. A spike without an epic has nothing to check here.

3. **Revalidate the Done when.** Read the Evidence comment of the spike: re-run each `ran:` command and re-read each `read:` source, and check that they still give what was noted. Run only commands that read; when one would write, stop and ask. When something no longer holds, leave a drift comment and stop: a spike in Backlog stays there. A spike already in Implement is resumed, so for it do this step after step 7.

4. **Check the project is ready** with this command, the Summary in single quotes and an inner `'` written `'\''`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --check spike <KEY> '<Summary>'
   ```

   When it refuses, relay its reason and stop.

5. **Find the folder of the findings.** Read the space of `atlassian.json` above with `getConfluenceSpaces` (its `id` and `homepageId`) and the descendants of its home with `getConfluencePageDescendants` and `depth: 3`, which reaches the pages inside `Spikes`. The folder is the `Spikes` of type `folder` whose parent is the `Work` of type `folder`. Keep the page of the descendants whose parent is `Spikes` and whose title starts with the spike's key and a space: it is the live doc of this spike, when it exists; when more than one matches, stop and name them. When either is missing, stop, writing nothing and naming which one is missing: the person creates them before the spike starts.

6. **Mark it Implement,** only when it is in Backlog: a spike already in Implement is resumed, so skip this step. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason, create no branch and run no more commands.

7. **Open the worktree** with the same arguments and `--worktree` instead of `--check`:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/branch.py --worktree spike <KEY> '<Summary>'
   ```

   It prints the branch and, on a second line, the folder `.claude/worktrees/<KEY>`, where the branch lives without an upstream. This skill never pushes the branch: the findings live in Confluence.

8. **Plan in plan mode.** The plan names, for each criterion of the Done when of the spike, the experiment that answers it and what each outcome would show. When an experiment needs personal data (the email, name or account of the person, such as the contact an API asks for in its `User-Agent`), ask the person for it before the plan is final, and name in the plan the variable that will carry it. Edit and run nothing until the person approves it; without plan mode, present the plan and wait.

9. **Run the approved experiments inside the worktree,** working in `.claude/worktrees/<KEY>` only (`git -C` for git, the folder as the working directory for everything else), and commit the experimental work in the spike branch in the commit format of the Gemba Code context. Keep each command and its literal output for the findings. Personal data the person gave reaches the experiment only through an environment variable set when the command runs: it is never written in a file of the worktree, in a commit or in a command you keep, which names the variable instead, and its value is replaced by that name in every output you keep.

   The time worked starts at the last change into Implement: read it once with `getJiraIssue`, asking only for `status` and `expand: "changelog"`. Before each experiment run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>` and compare its `minutes` with the time-box: the `originalEstimateSeconds` of step 2, divided by 60; a spike without an original estimate has no time-box to reach. When `minutes` has reached it, run no more experiments and go on to step 10 with what you have; the Answer is Inconclusa unless what you have already answers the question.

   When an experiment contradicts a criterion of the Done when of the spike, leave a drift comment and stop: publish nothing.

10. **Publish the findings.** Write them with the template above: the title `<KEY> <Summary>` and the first paragraph of the description of the spike as it was read, the Answer, the Evidence with every `ran:` and `read:` of the experiments and the literal output of each, with the name of the variable where the output held personal data, and the Next. Check the draft with this command, run alone and exactly in this form, and fix each problem it names until it passes:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/findings.py --site <site> --key <KEY> <<'FINDINGS'
    <the draft>
    FINDINGS
    ```

    When step 5 kept a page for this spike, update it with `updateConfluencePage`: its `id` as `pageId`, the `title` and the `body` the script printed as HTML (`contentFormat: "html"`), so the link to the issue stays. Otherwise create the page with `createConfluencePage`: the `id` of the space as `spaceId`, the `id` of the `Spikes` folder as `parentId`, `subtype: live`, the `title` the script printed and its `body` as HTML (`contentFormat: "html"`).

11. **Report** each Done when criterion of the spike with its evidence in the form `ran:` or `read:`, the Answer, and the link to the page.

12. **Register the time of the phase.** Take the time of the last change into Implement that step 9 read. Run:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phase_time.py --start <that time>
    ```

    It prints `timeSpent` and `started`. Write the worklog with `addWorklogToJiraIssue`, with that `timeSpent` and `started` and no comment, and say the time it registered.

## Leave a drift comment

Add it to the spike with `addCommentToJiraIssue` and `contentFormat: "markdown"`, following the drift template above, with its labels in English and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Name each criterion that changes.

## Cancel the spike

When the person decides to cancel the spike, in the request or after a stop of this skill, and it is in Backlog or Implement, write the cancellation comment of the template above instead of a drift comment, and check it with this command, run alone and exactly in this form, fixing each problem it names until it passes:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py --site <site> <<'CANCELLED'
<the comment>
CANCELLED
```

Read the transitions with `getTransitionsForJiraIssue`: when none has Cancelled as its destination (`to.name`), say so and stop, writing nothing. Then add what the command printed to the spike with `addCommentToJiraIssue` as HTML (`contentFormat: "html"`), and apply with `transitionJiraIssue` the one whose destination is Cancelled: pick it by destination, never by id. When it returns an error, stop: relay Jira's reason and say that the comment is already on the spike. Before the Implement mark, do not mark it Implement and do not create the branch; after it, leave the branch as it is and register the time of the phase as **Register the time of the phase** says. Then stop. A spike in any other status is not cancelled here: say its status and stop.
