---
name: project-create
description: Frames a new product with the person and writes its vision as a live doc at the root of the Confluence space, with its Purpose in CLAUDE.md. Asks first who originates the demand (Client, Market, Internal or Platform), lists the points of any shared material before framing, frames the problem, users, success and constraints one decision at a time, orders the risks with their kind, evidence, validation and threshold, records the go or no-go decision and checks the draft against the vision template. Use when the user wants to start a product from scratch, frame an idea before building it, or write its vision. It writes only what the person accepted, and creates no work item, fix version, requirements or roadmap.
argument-hint: "[idea or path to shared material]"
disable-model-invocation: true
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/vision.py *)
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

This skill writes one Confluence page, `Vision`, and the `## Purpose` section of `CLAUDE.md`, and only what the person accepted. It creates and edits no work item, fix version or other page. The `site` in `atlassian.json` above is the `cloudId` of every Atlassian call, `confluence.space` the space of the page.

The person decides. Ask one decision at a time with `AskUserQuestion`, offering two or three options with their reason, the recommended one first. A fact about the world carries its source or is a hypothesis. Never present your own opinion, desk research or synthetic users as evidence that someone needs or would pay for the product.

1. **Check the project.** When `atlassian.json` above is `(missing)`, or `CLAUDE.md` above has no `# Gemba` block, reply that the project needs `/gemba:setup` first and stop, without calling Confluence.

2. **Find the root.** Read the space of `atlassian.json` with `getConfluenceSpaces` (its `id` and `homepageId`) and the children of its home with `getConfluencePageDescendants` and `depth: 1`. When one of them is titled `Vision`, stop, writing nothing and giving its link: reviewing a framed product is not done here.

3. **Ask who originates the demand,** as the first question, with these four options:
   - `Client`: a client commissions and pays for it.
   - `Market`: the person builds it to sell it, as their own product or a SaaS.
   - `Internal`: it is for the person's own organization.
   - `Platform`: other development teams consume it.

   The origin decides who validates and how each fact is born: with `Market`, what the person says is a hypothesis until real people show it.

4. **Read the material first.** When the person shared material (notes, a PDF, minutes, a specification), read it and list each of its points, with what is known and who confirms it, before the first question of the frame, so no question asks what is already written.

5. **Frame the product,** one decision at a time:
   - the idea, rewritten in one sentence and confirmed;
   - users and problem together, as who cannot do what because of what; the segment is defined by the trigger that makes it change, not by its profile, and with `Market` it is a single segment of early adopters;
   - `Today`: what is used today in its place, doing nothing included, researched with sources;
   - success as a directional outcome, with its metrics, `Baseline` and `Target`; an unknown `Baseline` is written `desconocido` in the `Content:` language;
   - the fixed constraints: for each one ask what happens if it is not met. An external consequence (law, contract, a date with money at stake, a missing skill) makes it a constraint; a preference is not written.

   For each point that looks like a limit, ask whether the product never does it or does not do it yet: a never is a sentence of the vision; a not yet is left out of this page.

6. **Order the risks** after the frame. Each one carries its `Kind` (`Value`, `Usability`, `Feasibility` or `Viability`), `Evidence` or `Hypothesis`, how it is validated and the `Threshold` that validates it, set before testing. `Evidence` is a fact observed with real people or stated by a source; desk research gives evidence only of market facts such as published prices or competitors. With `Market`, every `Value` and `Viability` risk without evidence from real people is a `Hypothesis`. Propose the order from the greatest risk, the one with the least evidence and the most damage if it fails, and ask the person to confirm which one is the greatest: it goes first.

7. **Record the decision:** go to build, go to validate or no-go, who decides and the date. Propose go to build only when every `Value` and `Viability` risk has `Evidence`; otherwise propose go to validate, where the first version validates the greatest risk. The account of who decides comes from `atlassianUserInfo`, or from `lookupJiraAccountId` when someone else decides. When the person does not decide yet, the draft has no `### Decision` and the page no decision.

8. **Write the draft** with the template above, in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none; headings, labels and lozenges stay in English. Check it with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/vision.py <<'VISION'
   <the draft>
   VISION
   ```

9. **Ask the person to accept** the draft and the `## Purpose` section of step 11, shown in full. Write nothing they did not accept; with a correction, apply it, check the draft again and ask again.

10. **Publish the page** with `createConfluencePage`: the `id` of the space as `spaceId`, its `homepageId` as `parentId`, `subtype: live`, the `title` the script printed and its `body` as ADF (`contentFormat: "adf"`).

11. **Write the Purpose.** Add to `CLAUDE.md` with Edit, without retyping the rest, a `## Purpose` section inside the `# Gemba` block, right after its `## Language` section: the first sentence of the vision without its origin, and on its own line `Vision: <the link to the page>`.

12. **Reply** with the link to the page and what was written.
