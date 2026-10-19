---
name: epic-close
description: Closes a reviewed epic from Jira. Marks the epic Done once it is in Review, without waiting for the work items linked to it with Relates. It touches no branch and no code, merges and pushes nothing, and writes no worklog. Use when the user asks to close or finish an epic, or gives an epic key whose review is done.
disable-model-invocation: true
argument-hint: "[epic key]"
allowed-tools:
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Epic close

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

The only write of this skill is the Done mark: it creates, deletes, merges and pushes no branch, and writes no comment and no worklog. The `site` in `atlassian.json` above is the `cloudId` of every Jira call. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getJiraIssue getTransitionsForJiraIssue transitionJiraIssue
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the epic.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype` and `status`. Stop, writing nothing and naming it, when:
   - it is not an Epic: say its type;
   - its status is not Review: say its status.

   Read nothing else: its children were checked by `epic-review` before the Review mark, and the work items linked to it with Relates are work of their own, so the close does not wait for them.

3. **Mark it Done.** Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Done: pick it by destination, never by id.

   When no transition has Done as its destination, or `transitionJiraIssue` returns an error, stop right there: say so or relay Jira's reason.

4. **Report** the key and the link of the epic and its status. This skill writes no worklog: the time is registered by the phases of its children.
