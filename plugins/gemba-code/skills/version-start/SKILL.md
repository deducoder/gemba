---
name: version-start
description: Defines the next version of a framed product with the person and writes its page under Roadmap in Confluence as a live doc. Stops when the Vision has no go decision, takes a Next entry of the Roadmap, proposes the Unassigned requirements of the version in batches and resolves the open questions that block them, proposes the stack in the first version with research and writes it in CLAUDE.md, estimates each requirement and computes the release date in working days from the people who build it and the longest chain of dependencies, proposes the version name, checks in Jira the fix version the person created, and moves the requirements to their version in Requirements and the entry from Next to Now in Roadmap. Use when the user wants to plan, start or define the next version, release or MVP of a product framed with project-create. It declares no work item and creates no fix version.
argument-hint: "[Next entry of the roadmap]"
disable-model-invocation: true
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/release_date.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/version.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py *)
---

# Version start

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

CLAUDE.md:

```
!`cat "${CLAUDE_PROJECT_DIR}/CLAUDE.md" 2>/dev/null || echo "(missing)"`
```

Version template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/version.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/estimate.md`

This skill writes one new Confluence page, `<Product> vX.Y.Z` under `Roadmap`, updates `Requirements` and `Roadmap`, and writes the `## Stack` section of `CLAUDE.md`, and only what the person accepted. It creates and edits no work item and no fix version: the person creates the fix version in Jira. The `site` in `atlassian.json` above is the `cloudId` of every Atlassian call, `jira.project` the project and `confluence.space` the space of the pages.

The person decides. Ask one decision at a time with `AskUserQuestion`, offering two or three options with their reason, the recommended one first.

1. **Check the project.** When `atlassian.json` above is `(missing)`, or `CLAUDE.md` above has no `# Gemba` block, reply that the project needs `/gemba:setup` first and stop, without calling Atlassian.

2. **Read the product.** Read the space of `atlassian.json` with `getConfluenceSpaces` (its `id` and `homepageId`) and the children of its home with `getConfluencePageDescendants` and `depth: 1`, following its `cursor` until the last page. Without a page titled `Vision`, reply that the product needs `/gemba-code:project-create` first and stop. Read `Vision` with `getConfluencePage` and `contentFormat: "adf"` and, in the same message, its children with `getConfluencePageDescendants` on it; then `Requirements` and `Roadmap` the same way, both in one message.

3. **Check the decision.** The decision is the `panel` after the `Decision` heading of `Vision`. Without that panel, or with `panelType` `error` (no-go), reply that the product has no go decision, name which case it is, suggest deciding it with `/gemba-code:project-create` and stop, writing nothing. With `warning` (go to validate), the first version validates the greatest risk, the first of `Risks`; with `success` (go to build), it is the cut the person chooses.

4. **Name the version.** Find the id of the issue type Epic with `getJiraProjectIssueTypesMetadata` and read the `allowedValues` of `fixVersions` with `getJiraIssueTypeMetaWithFields` and `requiredFieldsOnly: false`. The versions of the product are those named `<Product> vX.Y.Z`. Without any, the version is the first one: `<Product>` is the `name` in the `allowedValues` of the field `project` of the same response, and the version `<Product> v0.1.0`. With versions, it is their `<Product>` with the highest minor plus one and patch `0`. Propose that name; the person accepts it or gives another of the same form.

5. **Choose the goal.** Offer the entries of `Next` in `Roadmap`, the one the argument names first: the chosen one is the goal of the version and moves to `Now`.

6. **Choose the requirements.** Propose the `Unassigned` requirements of `Requirements` that reach the goal, in batches: one `AskUserQuestion` question with `multiSelect` per batch of up to four requirements, each option one requirement with its ID and `Type`. The person keeps what enters the version. A new requirement the person names gets the number above the highest of the page, withdrawn ones included.

7. **Resolve the questions that block it.** Each `Open` question whose `Affects` names a requirement of the version, or that the person says changes it, blocks it: add `Blocks <the version>.` after its `Affects`, ask it one at a time, and with the answer add `Answer: <the answer>.` after it and mark it `[Answered]`. What the answer changes is written in the requirements it affects, which keep their IDs. A question the person cannot answer yet keeps the version from going on: say which one and stop, writing nothing. Nothing goes on to the date while a blocking question is `Open`.

8. **Choose the stack,** only in the first version and when `CLAUDE.md` above has no `## Stack`. Run `/gemba-code:research` with the question of which stacks meet the requirements of the version and the constraints of `Vision`, then offer two or three of the stacks its answer supports, each with its reason and the recommended one first. Write the chosen one with Edit, without retyping the rest, as a `## Stack` section inside the `# Gemba` block, right after its `## Purpose` section or, without one, after `## Language`: one bullet per layer, `- <layer>: <choice>`, and after a blank line `Research: <the link to the research page>`.

9. **Compute the release date.** Estimate each requirement of the version with the `## Epic` rule of the estimate above, the working time of the requirement, and propose which requirements of the version each one comes after. Ask how many people build the version. Run, alone and exactly in this form, with today as `start`:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/release_date.py <<'PLAN'
   {"start": "<YYYY-MM-DD>", "people": <n>, "requirements": [{"id": "R-nn", "estimate": "<1d 4h>", "after": ["R-nn"]}]}
   PLAN
   ```

   Show the person its `workingDays`, `releaseDate` and `longestChain`, with each estimate. With a correction, run it again.

10. **Write the drafts** in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none; headings, labels and lozenges stay in English.
    - The version page, with the template above: `[Planned]` and the `releaseDate`, the goal, the `MVP criterion` only in the first version (the risk it validates, from `Vision`, why this cut and what it leaves out), the `Outcome` with its `Baseline` and `Target`, the requirements of the version as the catalog writes them without their `Source` or `Type`, and the numbers of the questions of step 7, or one sentence saying none blocked it. Check it, alone and exactly in this form, with the link to `Requirements`:

      ```
      python3 ${CLAUDE_SKILL_DIR}/scripts/version.py --project <jira.project> --requirements <the link to Requirements> <<'VERSION'
      <the version draft>
      VERSION
      ```

    - `Requirements`, whole, from the page as published: a `### <the version>` section before `### Unassigned`, with the requirements of the version moved out of `Unassigned` in ascending order, and the questions of step 7 as they were answered. Check it, alone and exactly in this form, with the IDs the published page has:

      ```
      python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py --existing <the published IDs, comma separated> <<'REQUIREMENTS'
      <the requirements draft>
      REQUIREMENTS
      ```

    - `Roadmap`, whole, from the page as published: `Now` with `* [<the version>](<the link to the version page>) [Planned] · <releaseDate> <goal> Target: <the Target of the Outcome>`, and `Next` without the entry of step 5. The link is not known before the version page exists, so check the draft with `https://<site>/wiki` in its place now, and again with the link before publishing it:

      ```
      python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py <<'ROADMAP'
      <the roadmap draft>
      ROADMAP
      ```

    Each command runs alone, as its own Bash call; the three can go in one message. Fix each problem a command names until it passes.

11. **Check the fix version.** Ask the person to create in Jira, in Releases, the version with the name of step 4 and the `releaseDate` of step 9 as its release date. When they say it is created, read the `allowedValues` of `fixVersions` again with `getJiraIssueTypeMetaWithFields` and the id of Epic from step 4: the version exists, is neither released nor archived, and its `releaseDate` is the one of step 9. When one of them fails, say which and ask again; write nothing until it holds.

12. **Ask the person to accept** the three drafts, shown in full. Write nothing they did not accept; with a correction, apply it, check the draft again and ask again.

13. **Publish,** in this order, and when a call fails, stop and say what was published and what was not, without creating again a page that exists:
    1. The version page with `createConfluencePage`, the `id` of the space as `spaceId`, `subtype: live`, the `id` of `Roadmap` as `parentId`, and the `title` and `body` its script printed (`contentFormat: "adf"`).
    2. `Requirements` and `Roadmap`, the roadmap checked again with the link to the version page. Merge each one, alone and exactly in this form, with its published body, the body its script printed and the headings it changes: for `Requirements` the version, `Unassigned` and `Assumptions and open questions` when a question changed; for `Roadmap`, `Now` and `Next`:

       ```
       python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py <<'MERGE'
       {"live": <the published body>, "new": <the body the script printed>, "replace": [<the changed sections>]}
       MERGE
       ```

       Update the page with `updateConfluencePage`, its `id` as `pageId`, its title and the document the merge printed as its `body` (`contentFormat: "adf"`).

    The two merges can go in one message, and then the two updates. A live doc saves late: read each page until it has the change, up to three times, and retry the update once when it still does not; then say which page did not save.

14. **Reply** with the links to the version page, `Requirements` and `Roadmap`, the `releaseDate` with its working days and the chain that sets it, and the stack when it was written.
