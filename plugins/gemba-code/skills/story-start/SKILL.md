---
name: story-start
description: Declares a story in Jira from an idea. Reads the code the idea touches, drafts the story with its Done when and the evidence behind each criterion, and creates it in Backlog. Use when the user asks for a feature or a change to build ("make it…", "add…", "haz que…"), or asks to declare, define or write a story. Not for a small edit that needs no work item, an open question to research, or something that is broken. It starts no work.
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

The story stays in Backlog: this skill changes no status and creates no branch. The `site` in `atlassian.json` above is the `cloudId` of every Jira call, and its `jira.project` the project.

1. **Observe before drafting.** Read the code, documentation and history the idea touches, run the commands that already exist (tests, `--help`), and check against its source every command, file, field or option a criterion will name, until you are sure the story can be built.

2. **Ask, in one message, only the decisions the request leaves open (scope, options) and you cannot deduce.** Ask nothing when nothing is missing.

3. **Draft the story** with the template, with 8 Done when criteria at most, each one a behavior someone can check from outside: its headings, labels and Summary in English, and the rest in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none.
   - Wrap in `==` each Done when criterion the user did not ask for, so it reaches Jira in orange. A criterion that restates the request stays plain.
   - Give each criterion, in the same order, its Evidence line: the command you ran in step 1 with its output, or the source you read. The Evidence reaches Jira as a comment, not in the description.
   - Write in Out of scope what is excluded. Add `→ <KEY>` only when another work item already covers it; read that key first.

4. **Give it a priority and an original estimate** with the rules above.

5. **Check the draft** with this command, run alone and exactly in this form, and fix each problem it names until it passes:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/story.py --site <site> <<'STORY'
   <the draft>
   STORY
   ```

   When it asks to split the story, create nothing yet: propose in the conversation how to split it into stories of 8 criteria at most, grouped by the behaviors they check, each with its Summary and its criteria, and stop until the user agrees. With the agreement, check, create and comment each agreed story as in this step and the next, and link them with `createIssueLink`: `Blocks` where one cannot start before another is done, `Relates` between the rest.

6. **Create the story** with `createJiraIssue`: the project, the issue type Story, the `summary` and the `description` the script printed, the description as ADF (`contentFormat: "adf"`), and in `additional_fields` its `priority` and its `timetracking.originalEstimate`. Then add the `comment` the script printed to the new story with `addCommentToJiraIssue`, as ADF.

7. **Reply** with the key and link of each story it created, and nothing else.
