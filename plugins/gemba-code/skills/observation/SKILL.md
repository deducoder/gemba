---
name: observation
description: Finds the project's Observations database in Confluence and records or declares a row in it. Invoked by story-review, bug-review and epic-review to record a finding that stays out of its branch or below the threshold for its own work item; invoked by bug-start, story-start and spike-start to declare a row once its idea becomes a work item. Stops, writing nothing, when the database is missing, or when declare finds no row or more than one matching the reference given.
argument-hint: "record <KEY>: <observation> | declare <KEY> <reference>"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Observation

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/severity.md`

This skill only touches the Observations database: it creates no work item, changes nothing in Jira and edits no file of the project. The `site` in `atlassian.json` above is the `cloudId` of every Confluence call, `confluence.space` the space of the database. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getConfluenceSpaces getConfluencePageDescendants getConfluenceDatabase updateConfluenceDatabase
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Confluence.

2. **Read the request.** It is `record <KEY>: <observation>` or `declare <KEY> <reference>`. Without one of those two forms, ask for it.

3. **Find the database.** Read the space of `atlassian.json` above with `getConfluenceSpaces` (its `id` and `homepageId`) and the descendants of its home with `getConfluencePageDescendants` and `depth: 2`, which reaches `Work` and its children. Keep the child of `Work` named `Observations`, of `type: database`. When it is missing, stop, writing nothing: the person runs `/gemba:setup` first.

4. **Read it** with `getConfluenceDatabase`: its fields, its rows and its `snapshotToken`.

5. **Record**, when the request is `record <KEY>: <observation>`:
   - Decide its Severity with the rubric above.
   - Build one `add_entry`, at the position after the last row of step 4: `Observation` the text, `Severity` as decided, `Status` `Open`, `Origin` `https://<site>/browse/<KEY>`, `Date` today (`YYYY-MM-DD`), `Tracked in` `""`.
   - Apply it with `updateConfluenceDatabase`: the `contentId` and `snapshotToken` of step 4, `body.format: "csv"`, the envelope as `body.value`, and `body.context.content` the CSV step 4 read — without it the call is rejected.
   - Reply with the row and its Severity.

6. **Declare**, when the request is `declare <KEY> <reference>`:
   - Keep the one row of step 4 whose `Observation` contains `<reference>`, or whose `_id` equals it. Stop, naming them, when none match or more than one does.
   - Build one `edit_entry` for that row's position: `Status` `Declared`, `Tracked in` `https://<site>/browse/<KEY>`, every other cell `""` (unchanged).
   - Apply it the same way step 5 does.
   - Reply with the row and its new Status.
