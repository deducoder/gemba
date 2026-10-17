---
name: epic-start
description: Declares an epic in Jira from a deliverable. Reads the code the deliverable touches, proposes in plan mode the epic with its Done when, the stories and spikes that cover each criterion and a due date within its fix version, creates the epic in Backlog once the plan is approved and declares each child under it with story-start or spike-start, linking their Blocks. Use when the user asks to declare, plan, define or write an epic, or describes a deliverable too big for one story that commits to a date or a version. Not for one story, an open question to research, or something that is broken. It starts no work and assigns no one.
argument-hint: "[deliverable]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/epic.py *)
---

# Epic start

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/epic.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/priority.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/estimate.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/out-of-scope.md`

The epic and its children stay in Backlog: this skill changes no status, creates no branch and assigns no one. It creates the epic itself, and each child only through `story-start` or `spike-start`. Nothing is written in Jira before the plan is approved. A conversation in which this skill already created the epic goes on with the children not yet declared, and does not create the epic again. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read each work item key the request names** with `getJiraIssue`, all in one batch, before anything else.
   - A key that cannot be read stops the skill: create nothing, and reply with the key and Jira's reason.
   - A key that is already an Epic stops the skill: create and edit nothing, and reply with its key and its link. The epic this skill created earlier in the conversation does not stop it: go on from step 11 with the children not yet declared.
   - A key named for any other reason is context for the deliverable: the epic is drafted with what it says, and gets no link.

3. **Observe before planning.** Read the code, documentation and history the deliverable touches, and run the commands that already exist (tests, `--help`), until you know which stories and spikes it takes.

4. **Read the fix version.** Find the id of the issue type Epic with `getJiraProjectIssueTypesMetadata`, then read its fields with `getJiraIssueTypeMetaWithFields` and `requiredFieldsOnly: false`. Of the `allowedValues` of `fixVersions`, take the version the request names or, without one, the version neither released nor archived whose `releaseDate` is the earliest that has not passed, and keep its `releaseDate`. When the version named is released or archived, or no version qualifies, ask for one in the plan and do not make one up.

5. **Draft the epic** with the template, with 8 Done when criteria at most: its headings, labels and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none. Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. Write in Out of scope only what the Out of scope rules above allow. Check it with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/epic.py --site <site> <<'EPIC'
   <the draft>
   EPIC
   ```

6. **List its children**, only stories and spikes, each with its type, its Summary, its priority by the rules above for its type, the children it blocks (`Blocks`, only where one cannot start before another), a tentative estimate (the estimate rules above for its type: Story, or Spike for a time-box) and the Done when criterion of the epic it covers. Every criterion is covered by at least one child. A proposed child that describes a failure of something that already exists does not enter the plan: name it as a bug for `/gemba-code:bug-start`, and take out of Done when a criterion only that bug would cover.

7. **Propose the due date** as you propose an estimate: today plus the sum of the tentative estimates of the children, in working days, shown next to both references, the sum and the `releaseDate` of the fix version. It never falls after the `releaseDate`: when the sum does not fit before it, propose the `releaseDate` and say the children do not fit, so the person can cut children or pick another version. A version without `releaseDate` only gets a warning. A due date the person gives after the `releaseDate` is not accepted: ask for another date or another version.

8. **Give the epic a priority** with the Epic rules of the priority above.

9. **Present the plan in plan mode** and wait for the approval: the epic as the script accepted it, its fix version, its priority, its due date with both references, its children and the bugs named instead. Without plan mode, present the plan and wait. A change the person asks for goes back to the step it touches, and the plan is presented again.

10. **Create the epic** once the plan is approved, with `createJiraIssue`: the project, the issue type Epic, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), and in `additional_fields` `{"priority": {"name": "<level>"}, "fixVersions": [{"name": "<version>"}], "duedate": "<YYYY-MM-DD>"}`, with no original estimate and no component.

11. **Declare the children** in the order of the plan, one at a time. For each, invoke with the Skill tool `gemba-code:story-start` for a story or `gemba-code:spike-start` for a spike, with a request that names the epic's key and the child as the approved plan states it (its Summary and the Done when criterion of the epic it covers), and not its `Blocks`. The start makes the epic the parent of what it creates, and its own rules decide its priority and its estimate.
    - What a start asks, such as an open decision or a split of the story, goes to the person: relay it and wait for the answer, then let the start finish and go on with the next child.
    - A child its start does not create, because it names a bug, a spike, another story or an answer instead, is kept with what its start proposed, and the next child follows.
    - A start's reply ends that child, not this skill: keep the key and the link of each work item it created.

12. **Link the blocks** of the plan with `createIssueLink`, type `Blocks`, between the keys created: the blocking child as `inwardIssue` and the blocked one as `outwardIssue`. A child its start split into several stories or spikes takes its `Blocks` to each part, both as the blocking and as the blocked child. A `Blocks` whose other child was not created is not linked.

13. **Reply** with the key and the link of the epic and of each child created, the `Blocks` linked, each child of the plan that was not created with what its start proposed, each `Blocks` left without a link, and the bugs the plan named for `/gemba-code:bug-start`, and nothing else.
