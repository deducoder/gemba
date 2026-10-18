# Estimate

The original estimate is the working time of the person with Claude in Implement and Review, written in Jira's units of time: `w`, `d`, `h` and `m`. Decide it from two questions: whether the change follows something that already exists in the project, and how much has to be observed and how uncertain it is. Work out the number from your answers, and never give it by size alone: a work item is not split, and a spike is not narrowed, because of its estimate.

## Story

What the story builds and what shows each of its Done when criteria. A story that follows a sibling skill, template or script needs little: the pattern is read and applied. A story of new behavior needs more as it has more criteria to show, more cases of eval to write and run, and more files with no model to follow.

## Epic

Its due date is the working time of the requirement the epic delivers: what its Done when criteria ask to have working, answered with the same two questions, never the sum of the estimates of its children. The children are cut from the requirement afterwards, within that date. A requirement that fits in one working day gets the same day as its due date.

## Window of an epic

A story or a spike whose parent is an epic with a `duedate` reads the `originalEstimate` of the children the epic already has. The window it leaves is the working time from today to the `duedate`, minus those estimates. The window is a reference for the estimate, never a limit: when the estimate the work item needs does not fit in it, the work item keeps that estimate and the reply says that the children no longer fit the date of the epic.

## Bug

What the fix changes and what has to run again. A bug that is fixed with one instruction or one line needs little. A bug with several Neighboring inputs to run on the fixed code, or a Root cause that touches several files, needs more.

## Spike

What must be observed to answer the question. It is the time-box: the working time the research may take before it answers. A question answered by reading one source needs little. One that needs several sources, experiments or comparisons, or whose outcome is uncertain, needs more.
