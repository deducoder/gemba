---
name: spike-start
description: Declares a spike in Jira from a closed question whose answer a decision waits on. Checks that the project does not answer it already, sends a question answered by reading sources to research, drafts the spike with the question, its decision, its Done when and its time-box, and creates it in Backlog with the evidence in a comment. Use when the user asks to declare, open or write a spike, or asks to find out whether something nobody has verified works ("can X do Y?", "find out whether…", "investiga si…"). It declares the question and does not answer it. Not for a question answered by reading sources, something to build or something that is broken.
argument-hint: "[question]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/spike.py *)
---

# Spike start

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/spike.md`
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/priority.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/estimate.md`

!`cat ${CLAUDE_PLUGIN_ROOT}/references/out-of-scope.md`

The spike stays in Backlog: this skill answers nothing, changes no status, creates no branch and creates no work item other than a spike. The research belongs to the spike once it is implemented, so declaring it runs no experiment. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

A request with two questions or more is one spike per question. **Observe before drafting** decides each question on its own, so one can be answered, be a research or be a story while another becomes a spike; **Ask** is one message for all of them; from **Draft the spike** on, each question that is a spike goes through the steps on its own, with its own decision, Evidence, priority and time-box, each Evidence with only the lines that observed its question, and the epic of step 2 as the parent of each. Do not wait for an agreement to split them.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read each work item key the request names** with `getJiraIssue`, all in one batch, before anything else.
   - An Epic of the project in Backlog is the parent of the spike: ask `getJiraIssue` for its `duedate` too, and read the children it already has with `searchJiraIssuesUsingJql` (`parent = <KEY>`, every page, with their `status` and `timetracking`).
   - An Epic in another status, or of another project, is not: the spike goes without a parent, and the reply says why, with the epic's status.
   - A Spike stops the skill: create and edit nothing, and reply that it is already declared, with its key and its link.
   - Any other work item stops the skill: create and edit nothing, and reply with its key, its type and its link.

3. **Observe before drafting.** Read the documentation, code and history of the project the question touches, only to check that they do not answer it already, and keep each file you read as a `read:` line with its path and line and each command you ran as a `ran:` line with its output. Do not answer the question: search outside the project, try the service or build a prototype only when the spike is implemented. Then decide whether the request is a spike at all; when it is not, create nothing for it and reply with what it is instead:
   - **Answered** when the documentation, the code or the history of the project already answer the question: the answer with its source, as a `read:` line with its path and line.
   - **A research** when sources outside the project (official documentation, specifications, public code) answer the question and nothing has to be run: to answer with `/gemba-code:research`, naming the question. What a service or tool offers is read in its documentation, so it is a research; whether this project's code can use it, and anything to try, build or measure, needs an experiment, so it is a spike. Decide it from the wording of the question and from the project: do not call `WebSearch` or `WebFetch`.
   - **A story** when it describes something to build, not a question: to declare with `/gemba-code:story-start`.
   - **A bug** when it describes a failure of something that already exists: to declare with `/gemba-code:bug-start`.

4. **Ask, in one message, only what the question leaves open and you cannot deduce,** such as the decision that waits on its answer. Ask nothing when nothing is missing.

5. **Draft the spike** with the template: its headings, labels and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none.
   - The question is closed: a single question that the research answers with a yes, a no or an inconclusive result.
   - Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. A criterion that restates the request stays plain.
   - The Evidence holds the `ran:` and `read:` lines of **Observe before drafting**. It reaches Jira as a comment, not in the description.
   - Write in Out of scope only what the Out of scope rules above allow. The decision that waits on the answer, and the work that follows it, are why the spike exists, not something it excludes. Add `→ <KEY>` only when another work item already covers it; read that key first.

6. **Give it a priority and a time-box** with the Spike rules of the priority above and the Spike rules of the estimate above, and with the Window of an epic rule of the estimate above when the spike has an epic as parent: they set the time-box.

7. **Check the draft** with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/spike.py --site <site> <<'SPIKE'
   <the draft>
   SPIKE
   ```

8. **Create the spike** with `createJiraIssue`: the project, the issue type Spike, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), the key of the epic of step 2 as `parent` (a string) when it has one, and in `additional_fields` its priority and its time-box as `{"priority": {"name": "<level>"}, "timetracking": {"originalEstimate": "<time-box>"}}`. Then add the `comment` the script printed to the new spike with `addCommentToJiraIssue`, as ADF.

9. **Reply** with the key and link of each spike it created, the answer and its source for each question the project already answers, the research it named, with its question, the story or the bug it named instead, why an epic it named is not the parent and, when the time-box does not fit the window the epic leaves, that the children no longer fit its date, and nothing else.
