---
name: epic-review
description: Reviews a finished epic from Jira. Checks that each of its children is Done or Cancelled, marks it in Review, and reviews with /code-review the merge into develop of each of its stories in Done. It declares each finding loose with the start skill of its type, linked to the epic with Relates, and warns when the epic reaches Review after its due date. It stops, writing nothing, when the epic or a child is not ready, resumes one already in Review and writes no worklog. Use when the user asks to review an epic, or gives an epic key whose children are finished.
argument-hint: "[epic key]"
---

# Epic review

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Until the Review mark this skill only reads: it writes nothing in Jira and nothing in git. It has no branch, it adds no child to the epic and it writes no worklog. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the epic.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status` and `duedate`. Stop, writing nothing and naming it, when:
   - it is not an Epic: say its type;
   - its status is not Implement or Review: say its status.

3. **Read its children** with `searchJiraIssuesUsingJql`, the JQL `parent = <KEY>` and the fields `summary`, `issuetype` and `status`. When a child is not Done or Cancelled, stop, writing nothing, and name each such child with its key and its status.

4. **Mark it Review,** only when it is in Implement: an epic already in Review is resumed, so skip this step and go on from step 5. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Review: pick it by destination, never by id. This is the first write of the phase.

   When `transitionJiraIssue` returns an error, stop right there: relay Jira's reason and review no code.

5. **Warn about the due date.** When the epic has a `duedate` and today is later than it, say that the epic reached Review after its due date, naming the date, and go on: it does not stop the skill.

6. **Review the code of each story.** For each child that is a Story in Done, find its merge into `develop` with:

   ```
   git log --merges --format='%H %s' develop --grep "^Merge branch 'story/<child KEY>/"
   ```

   and invoke `/code-review <merge>^1..<merge>` with the Skill tool, `<merge>` being the hash it printed. Spikes are never merged and Cancelled children delivered nothing: skip both. When a story has no merge, name it. When no story has a merge, say so and review no code.

7. **Declare each finding loose.** For each finding of step 6 that you or the person do not dismiss, invoke with the Skill tool the start skill of its type, without naming the epic, so it gets no parent: `/gemba-code:bug-start` for something that fails, `/gemba-code:story-start` for something to build and `/gemba-code:spike-start` for a question to research. Then link the new work item to the epic with `createIssueLink`, the link type `Relates`. The epic gets no child: what its review finds is work of its own.

8. **Report** the children and their status, the merges reviewed, each finding with the key and link of the work item declared for it and the due date warning when there is one. This skill writes no worklog: each child registered the time of its own phases.
