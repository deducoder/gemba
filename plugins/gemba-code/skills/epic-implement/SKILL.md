---
name: epic-implement
description: Starts a declared epic from Jira. Checks that it is an Epic in Backlog or Implement with children, marks it in Implement, and lists its children ready to start, in Backlog and not blocked, by priority and with their assignee, together with its due date and the days left. It stops, writing nothing, when the epic is not ready, resumes one already in Implement, creates no branch and writes no worklog. Use when the user asks to start, implement or work on an epic, or gives an epic key to begin.
argument-hint: "[epic key]"
---

# Epic implement

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Today: !`date +%Y-%m-%d`

Until the Implement mark this skill only reads. It never creates a branch or pushes, it creates and edits no work item, and it writes no worklog and no original estimate on the epic: its children are built with their own skills. The `site` in `atlassian.json` above is the `cloudId` of every Jira call.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read the epic.** Without a key in the request, ask for it. Read it with `getJiraIssue`, asking for its `summary`, `issuetype`, `status` and `duedate`. Stop, writing nothing and naming it, when:
   - it is not an Epic: say its type;
   - its status is not Backlog or Implement: say its status.

3. **Read its children** with `searchJiraIssuesUsingJql`, the JQL `parent = <KEY>` and the fields `summary`, `issuetype`, `status`, `issuelinks`, `priority` and `assignee`, asking for the next page with its `nextPageToken` while `pageInfo.hasNextPage` is true. When it has no children, stop, writing nothing, and say that the epic has no children.

4. **Mark it Implement,** only when it is in Backlog: an epic already in Implement is resumed, so skip this step. Read the transitions with `getTransitionsForJiraIssue` and apply with `transitionJiraIssue` the one whose destination (`to.name`) is Implement: pick it by destination, never by id. This is the only write of this skill.

   When no transition has Implement as its destination, or `transitionJiraIssue` returns an error, stop right there: say so or relay Jira's reason, and list no children.

5. **List the ready children.** A child is ready when its status is Backlog and every link of type Blocks in which it is blocked (the other work item is its `inwardIssue`, "is blocked by") points to a work item in Done or Cancelled. Any other link, such as Relates, blocks nothing. Order them by priority, Highest, High, Medium, Low and Lowest, and by key number within the same priority. For each, give its key, its type, its Summary, its priority and its assignee (`assignee.displayName`), or "unassigned" when it has none. Name no child that is not ready: say only how many children are not ready, without counting those in Done or Cancelled. When no child is ready, say so: the epic stays marked.

6. **Show the due date** of the epic and the calendar days from today above to it. When it is today, say it is due today. When it is earlier than today, warn that the epic is overdue, naming the date, and go on: it does not stop the skill. When the epic has no due date, say so.

7. **Reply** with the status of the epic, the ready children of step 5 and the due date of step 6, and nothing else.
