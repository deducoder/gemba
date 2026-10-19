# Estimate

The original estimate is the working time of one person working with Claude Code and Gemba in Implement and Review, the time the worklogs of those phases register, written in Jira's units of time: `w`, `d`, `h` and `m`. It is not the pace of someone who writes the code without an agent. Never give it by size alone: a work item is not split, and a spike is not narrowed, because of its estimate.

Work it out with these principles:

1. **What was observed comes first.** Before estimating, read with `searchJiraIssuesUsingJql` up to 20 work items of the same type in Done that have time worked (`project = <KEY> AND issuetype = <Type> AND statusCategory = Done AND timespent is not EMPTY ORDER BY resolved DESC`, with their `summary` and `timetracking`). Their `timeSpent` is where the estimate starts, the closest in scope first. Their `originalEstimate` is no reference: it is what the time worked corrects.
2. **Without that history, add up the work of the phases.** Count the steps Implement and Review will take: what is read, what is changed, which tests and evals are written and run, the live test, and the decisions that wait on the person. Writing and editing with Claude takes little; what makes a phase longer is running tests, evals and live tests, and waiting for decisions.
3. **Name what is uncertain instead of padding it.** What is not known does not get a margin: it becomes what the work item has to observe, or a spike with its time-box.
4. **The sections below say which steps count for each type.**

## Story

What the story builds and what shows each of its Done when criteria. A story that follows a sibling skill, template or script needs little: the pattern is read and applied. A story of new behavior needs more as it has more criteria to show, more cases of eval to write and run, and more files with no model to follow.

## Epic

Its due date is the working time of the requirement the epic delivers: what its Done when criteria ask to have working, worked out the same way, never the sum of the estimates of its children. The children are cut from the requirement afterwards, within that date. A requirement that fits in one working day gets the same day as its due date.

## Due date

Only an epic and a loose story or spike get a due date. An epic always gets one, from its requirement as above. A story or a spike without an epic gets one only when the request states the external commitment behind the date (a contract, an event, a third party's date): a date without one is no due date, and a child of an epic never gets one.

## Window of an epic

A story or a spike whose parent is an epic with a `duedate` reads the `originalEstimate` of the children the epic already has that are not Done or Cancelled: the time of a finished child is already spent. The window it leaves is the working time from today to the `duedate`, minus those estimates. A child without `originalEstimate` counts for nothing, a `duedate` already past leaves no window, and an epic without `duedate` gives none. The window is a reference for the estimate, never a limit: when the estimate the work item needs does not fit in it, the work item keeps that estimate and the reply says that the children no longer fit the date of the epic.

## Bug

What the fix changes and what has to run again. A bug that is fixed with one instruction or one line needs little. A bug with several Neighboring inputs to run on the fixed code, or a Root cause that touches several files, needs more.

## Spike

What must be observed to answer the question. It is the time-box: the working time the research may take before it answers. A question answered by reading one source needs little. One that needs several sources, experiments or comparisons, or whose outcome is uncertain, needs more.
