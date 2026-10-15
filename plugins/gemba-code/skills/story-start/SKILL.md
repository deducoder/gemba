---
name: story-start
description: Declares a story in Jira from an idea. Reads the code the idea touches, drafts the story with its Done when and the evidence behind each criterion, and creates it in Backlog. Use when the user asks for a feature or a change to build ("make it…", "add…", "haz que…"), or asks to declare, define or write a story, and may name an epic key to nest it under. Not for a small edit that needs no work item, an open question to research, or something that is broken. It starts no work.
argument-hint: "[idea]"
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/story.py *)
---

# Story start

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

Template:

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/story.md`
```

!`cat ${CLAUDE_SKILL_DIR}/references/priority.md`

!`cat ${CLAUDE_SKILL_DIR}/references/estimate.md`

The story stays in Backlog: this skill changes no status, creates no branch and creates no work item other than a story. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

1. **Check the project.** When `atlassian.json` above is `(missing)`, reply that the project needs `/gemba:setup` first and stop, without calling Jira.

2. **Read each work item key the request names** with `getJiraIssue`, all in one batch, before anything else.
   - An Epic of the project in Backlog is the parent of the story.
   - An Epic in another status, or of another project, is not: the story goes without a parent, and the reply says why, with the epic's status.
   - Any other work item stops the skill: create and edit nothing, and reply with its key, its type and its link. When it is a Story, say it is already declared.

3. **Observe before drafting.** Read the code, documentation and history the idea touches, run the commands that already exist (tests, `--help`), and check against its source every command, file, field or option a criterion will name, until you are sure the story can be built. Then decide whether the idea is a story at all; when it is not, create nothing and reply with what it is instead:
   - **A bug** when it describes a failure of something that already exists: what fails and the evidence that shows it.
   - **A spike** when building it depends on how something outside the repository works (a service, an API, a library) and nobody has verified it: the spike with its closed question: a single question that a short research answers with a yes or a no, and no list of open ones.

4. **Ask, in one message, only the decisions the request leaves open (scope, options) and you cannot deduce.** Ask nothing when nothing is missing.

5. **Draft the story** with the template, with 8 Done when criteria at most, each one a behavior someone can check from outside: its headings, labels and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none.
   - Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. A criterion that restates the request stays plain.
   - Give each criterion, in the same order, its Evidence line: the command you ran in step 3 with its output, or the source you read. The Evidence reaches Jira as a comment, not in the description.
   - Write in Out of scope what is excluded. Add `→ <KEY>` only when another work item already covers it; read that key first, unless step 2 already did.

6. **Give it a priority and an original estimate** with the rules above.

7. **Check the draft** with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/story.py --site <site> <<'STORY'
   <the draft>
   STORY
   ```

   When it asks to split the story, create nothing yet: propose in the conversation how to split it into stories within the limit it names, grouped by the behaviors they check, each with its Summary and its criteria, and stop until the user agrees. With the agreement, check, create and comment each agreed story as in this step and the next, each with the parent of step 2 when it has one, and link them with `createIssueLink`: `Blocks` where one cannot start before another is done, `Relates` between the rest.

8. **Create the story** with `createJiraIssue`: the project, the issue type Story, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), the key of the epic of step 2 as `parent` (a string) when it has one, and in `additional_fields` its priority and its estimate as `{"priority": {"name": "<level>"}, "timetracking": {"originalEstimate": "<estimate>"}}`. Then add the `comment` the script printed to the new story with `addCommentToJiraIssue`, as ADF.

9. **Reply** with the key and link of each story it created, the spikes or bugs it named instead, and why an epic it named is not the parent, and nothing else.
