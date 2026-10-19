# Estimate

The original estimate is the working time of one person working with Claude Code and Gemba in Implement and Review, the time the worklogs of those phases register, written in Jira's units of time: `w`, `d`, `h` and `m`. Never give it by size alone: a work item is not split, and a spike is not narrowed, because of its estimate.

Work it out with these principles; the sections below say which steps count for each type.

1. **What was observed comes first.** Before estimating, read with `searchJiraIssuesUsingJql` up to 20 work items of the same type in Done that have time worked (`project = <KEY> AND issuetype = <Type> AND statusCategory = Done AND timespent is not EMPTY ORDER BY resolved DESC`, with their `summary` and `timetracking`). Their `timeSpent` is where the estimate starts, the closest in scope first. Ignore their `originalEstimate`. A history already read in this session for the same project and type, or carried by the request, is reused, not read again.
2. **Without that history, add up the work of the phases.** Count the steps Implement and Review will take: what is read, what is changed, which tests and evals are written and run, the live test, and the decisions that wait on the person. Writing and editing with Claude takes little; running and waiting take the time.
3. **Name what is uncertain instead of padding it.** What is not known does not get a margin: it becomes what the work item has to observe, or a spike with its time-box.

## Story

What the story builds and what shows each of its Done when criteria. The steps to count: the pattern to read and apply, the criteria to show, the eval cases to write and run, and the files with no model to follow.

## Epic

Its due date is the working time of the requirement the epic delivers: what its Done when criteria ask to have working, worked out with the principles above, never the sum of the estimates of its children. Epics register no time of their own, so the history to read is the stories and spikes of the epics in Done of the project, the `timeSpent` of each epic's children added up. The children are cut from the requirement afterwards, within that date. A requirement that fits in one working day gets the same day as its due date.

## Due date

Only an epic and a loose story or spike get a due date. An epic always gets one, from its requirement as above. A story or a spike without an epic gets one only when the request states the external commitment behind the date (a contract, an event, a third party's date): a date without one is no due date, and a child of an epic never gets one.

## Window of an epic

A story or a spike whose parent is an epic with a `duedate` reads the `originalEstimate` of the children the epic already has that are not Done or Cancelled: the time of a finished child is already spent. The window it leaves is the working time from today to the `duedate`, minus those estimates. A child without `originalEstimate` counts for nothing, a `duedate` already past leaves no window, and an epic without `duedate` gives none. The window is a reference for the estimate, never a limit: when the estimate the work item needs does not fit in it, the work item keeps that estimate and the reply says that the children no longer fit the date of the epic.

## Bug

What the fix changes and what has to run again. The steps to count: the files of the Root cause and the Neighboring inputs to run again on the fixed code.

## Spike

What must be observed to answer the question. It is the time-box: the working time the research may take before it answers. The steps to count: the sources to read and the experiments or comparisons to run.
