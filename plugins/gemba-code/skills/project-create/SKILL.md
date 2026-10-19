---
name: project-create
description: Frames a new product with the person, discovers its requirements and writes its Vision at the root of the Confluence space, with Requirements and Roadmap under it as live docs and its Purpose in CLAUDE.md. Asks first who originates the demand (Client, Market, Internal or Platform), lists the points of any shared material, frames problem, users, success and constraints one decision at a time, orders the risks, proposes the requirements in batches (functional, business rules, the Volere non-functional types, constraints, then the unsaid), turns what cannot be measured into open questions, records the go or no-go decision and checks each page against its template; with a framed product it reviews the three pages and changes only the sections that moved. Use when the user wants to start a product from scratch, frame an idea before building it, write its vision and requirements, or bring them up to date. It writes only what the person accepted, assigns no version and creates no work item or fix version.
argument-hint: "[idea or path to shared material]"
disable-model-invocation: true
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/vision.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Project create

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

CLAUDE.md:

```
!`cat "${CLAUDE_PROJECT_DIR}/CLAUDE.md" 2>/dev/null || echo "(missing)"`
```

Vision template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/vision.md`
```

Requirements template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/requirements.md`
```

Roadmap template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/roadmap.md`
```

This skill writes or updates three Confluence pages, `Vision`, `Requirements` and `Roadmap`, and the `## Purpose` section of `CLAUDE.md`, and only what the person accepted. It creates and edits no work item, fix version or other page, and assigns no requirement to a version. The `site` in `atlassian.json` above is the `cloudId` of every Atlassian call, `confluence.space` the space of the pages. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getConfluencePage updateConfluencePage createConfluencePage getConfluencePageDescendants getConfluenceSpaces lookupJiraAccountId
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

The person decides. Ask one decision at a time with `AskUserQuestion`, offering two or three options with their reason, the recommended one first. A fact about the world carries its source or is a hypothesis. Never present your own opinion, desk research or synthetic users as evidence that someone needs or would pay for the product.

1. **Check the project.** When `atlassian.json` above is `(missing)`, or `CLAUDE.md` above has no `# Gemba` block, reply that the project needs `/gemba:setup` first and stop, without calling Confluence.

2. **Find the root.** Read the space of `atlassian.json` with `getConfluenceSpaces` (its `id` and `homepageId`) and the children of its home with `getConfluencePageDescendants` and `depth: 1`, following its `cursor` until the last page. When one of them is titled `Vision`, the product is framed: follow **Review a framed product** below instead of the steps that follow.

3. **Ask who originates the demand,** as the first question, offering always these four options, even one that seems not to apply, with the recommended one first:
   - `Client`: a client commissions and pays for it.
   - `Market`: the person builds it to sell it, as their own product or a SaaS.
   - `Internal`: it is for the person's own organization.
   - `Platform`: other development teams consume it.

   The origin decides who validates and how each fact is born: with `Market`, what the person says is a hypothesis until real people show it.

4. **Read the material first.** When the person shared material (notes, a PDF, minutes, a specification), read it and list each of its points, numbered, with what is known and who confirms it, before the first question of the frame, so no question asks what is already written.

5. **Frame the product,** one decision at a time:
   - the idea, rewritten in one sentence and confirmed;
   - users and problem together, as who cannot do what because of what; the segment is defined by the trigger that makes it change, not by its profile, and with `Market` it is a single segment of early adopters;
   - `Today`: what is used today in its place, doing nothing included, researched with sources;
   - success as a directional outcome, with its metrics, `Baseline` and `Target`. A `Baseline` nobody has measured is written `desconocido` in the `Content:` language followed by `(Question n)`, and that question, with its assumption, goes to the open questions of step 7;
   - the fixed constraints: for each one ask what happens if it is not met. An external consequence (law, contract, a date with money at stake, a missing skill) makes it a constraint; a preference is not written.

   For each point that looks like a limit, ask whether the product never does it or does not do it yet: a never is a sentence of the vision; a not yet is a requirement of step 7.

6. **Order the risks** after the frame. Each one carries its `Kind` (`Value`, `Usability`, `Feasibility` or `Viability`), `Evidence` or `Hypothesis`, how it is validated and the `Threshold` that validates it, set before testing. `Evidence` is a fact observed with real people or stated by a source; desk research gives evidence only of market facts such as published prices or competitors. With `Market`, every `Value` and `Viability` risk without evidence from real people is a `Hypothesis`. Propose the order from the greatest risk, the one with the least evidence and the most damage if it fails, and ask the person to confirm which one is the greatest: it goes first.

7. **Discover the requirements** after the risks, in this order, one stage at a time:
   1. functional, walking the work of the main user from end to end, broad before deep, then the other users;
   2. business rules, from the variants and exceptions of that walk;
   3. non-functional, going through the eight Volere types one by one: look and feel, usability, performance, operational, maintainability, security, cultural and legal;
   4. constraints that ask for something concrete;
   5. last, what the person did not say: the "what if…?" of each user and each rule.

   Propose them in batches: one `AskUserQuestion` question with `multiSelect` per batch of up to four requirements, each option one requirement with its ID, `Type` and `Source`. The person keeps what they accept, unchecks what they remove and corrects with a note. Each requirement is singular and verifiable, with its fit criterion inside the sentence, and carries the next ID of one series from `R-01`, never reused (a proposal the person removes leaves its ID unused), its `Type` (`Functional`, `Business rule`, `Non-functional` or `Constraint`) and its `Source`: who said it, the point of the material or the person's hypothesis, which also gets `[Hypothesis]`. Every requirement is born in `Unassigned`. What cannot be written measurable yet is not a requirement: it becomes an open question, numbered from 1, with the assumption that holds until it is answered and the requirements it affects.

8. **Account for the material.** When there was material, show each of its points with where it ended: an `R-nn`, a `Question n` or a limit sentence of the vision. A point with nowhere to go is raised now; none is lost without saying so.

9. **Close the discovery** when there is a minimal definition: the problem, the users, a measurable success and the requirements that make the product valuable, usable and feasible, each risk with its validation and threshold. Ask the person to accept it as minimal; open questions do not stop it, the catalog needs not be complete, and the cut is theirs.

10. **Record the decision:** go to build, go to validate or no-go, who decides and the date. Propose go to build only when every `Value` and `Viability` risk has `Evidence`; otherwise propose go to validate, where the first version validates the greatest risk. The account of who decides comes from `atlassianUserInfo`, or from `lookupJiraAccountId` when someone else decides. When the person does not decide yet, the draft has no `### Decision` and the page no decision.

11. **Write the drafts** with the templates above, in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none; headings, labels and lozenges stay in English. The roadmap has no version yet: `Next` holds the first goal (with go to validate, validating the greatest risk) and `Later` what is known but not ordered. Each `Question n` the vision cites is a question of the requirements draft. Check each draft with its command, run alone and exactly in this form, and fix each problem it names until it passes:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/vision.py <<'VISION'
    <the vision draft>
    VISION
    ```

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py <<'REQUIREMENTS'
    <the requirements draft>
    REQUIREMENTS
    ```

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py <<'ROADMAP'
    <the roadmap draft>
    ROADMAP
    ```

12. **Ask the person to accept** the three drafts and the `## Purpose` section of step 14, shown in full. Write nothing they did not accept; with a correction, apply it, check the draft again and ask again.

13. **Publish the pages** with `createConfluencePage`, each with the `id` of the space as `spaceId`, `subtype: live`, the `title` its script printed and its `body` as ADF (`contentFormat: "adf"`): first `Vision` with the `homepageId` as `parentId`, then `Requirements` and `Roadmap` with the `id` of `Vision` as `parentId`. When the vision cites a `Question n`, check it again with the link to `Requirements`, run alone and exactly in this form, and update `Vision` with `updateConfluencePage` and the `body` it printed; a live doc saves late, so read the page and retry until it has the link. When a call fails, stop and say which pages were published and which were not, without creating again a page that exists:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/vision.py --requirements <the link to Requirements> <<'VISION'
    <the vision draft>
    VISION
    ```

14. **Write the Purpose.** Add to `CLAUDE.md` with Edit, without retyping the rest, a `## Purpose` section inside the `# Gemba` block, right after its `## Language` section: the first sentence of the vision without its origin, and after a blank line `Vision: <the link to the page>`.

15. **Reply** with the links to the three pages and what was written, and suggest `/gemba-code:version-start` to define the first version.

## Review a framed product

A framed product is reviewed, never framed again: only what moved changes, and only what the person accepts is written.

1. **Read the pages** with `getConfluencePage` and `contentFormat: "adf"`: `Vision`, then its children `Requirements` and `Roadmap` from `getConfluencePageDescendants` on it. When a child is missing, discover only what it holds (steps 7 to 9 for `Requirements`, the goals of step 11 for `Roadmap`), check its draft with its command, ask the person to accept it and create it with `createConfluencePage` and the `id` of `Vision` as `parentId`, before going on; `Vision` is not created again.

2. **Walk the pages in order,** `Vision`, `Requirements`, `Roadmap`, and for each one ask what moved since it was written, section by section, offering the sections as options. Propose a change only for a section where something moved, with the same rules as the framing: a new requirement takes the number above the highest of the page, withdrawn ones included, and is never reused; a withdrawn requirement moves to `Withdrawn` with its reason and today's date, and is never deleted; a new decision rewrites the panel with its color, `Decided by` and today's date. A section where nothing moved is left out of the proposal.

3. **Write the drafts** of the pages that change, whole, from the page as published plus the accepted changes, and check each one with its command from step 11, the vision with `--requirements <the link to Requirements>` as in step 13 so its questions keep their links. Check the requirements with the IDs the published page has, run alone and exactly in this form:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py --existing <the published IDs, comma separated> <<'REQUIREMENTS'
   <the requirements draft>
   REQUIREMENTS
   ```

4. **Ask the person to accept** each change, shown with the section as it is and as it would be. With nothing accepted, write nothing.

5. **Merge each page** that changes, run alone and exactly in this form, with its published body, the body its script printed and the headings of every section the accepted changes touch, `""` for the text above the first heading of `Vision`; a withdrawn requirement touches the section it leaves and `Withdrawn`, and a section the new body no longer has is removed:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py <<'MERGE'
   {"live": <the published body>, "new": <the body the script printed>, "replace": [<the accepted sections>]}
   MERGE
   ```

   Update the page with `updateConfluencePage`, its `id` as `pageId`, its title and the document the merge printed as its `body` (`contentFormat: "adf"`), then read it until it has the change. When the first sentence of the vision changed, update `## Purpose` in `CLAUDE.md` with Edit.

6. **Reply** with each page that changed, the sections changed in it and its link.
