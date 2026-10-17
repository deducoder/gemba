---
name: setup
description: Prepares a project for Gemba. Declares Gemba and the languages in CLAUDE.md, the Atlassian site, Jira space and Confluence space in .gemba/project/atlassian.json, how finished work reaches develop in .gemba/project/git.json, turns off commit and PR attribution, ignores the worktrees folder in .gitignore, and creates the initial git history. Safe to re-run.
disable-model-invocation: true
allowed-tools:
  - Read(/${CLAUDE_SKILL_DIR}/assets/*)
---

# Setup

## Current state

CLAUDE.md:

```
!`cat "${CLAUDE_PROJECT_DIR}/CLAUDE.md" 2>/dev/null || echo "(missing)"`
```

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

.gemba/project/git.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/git.json" 2>/dev/null || echo "(missing)"`
```

.claude/settings.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.claude/settings.json" 2>/dev/null || echo "(missing)"`
```

.gitignore:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gitignore" 2>/dev/null || echo "(missing)"`
```

Git:

```
!`git log --oneline -1 2>/dev/null && git branch -vv && git remote -v || echo "(no history)"`
```

## CLAUDE.md template

```markdown
!`cat ${CLAUDE_SKILL_DIR}/assets/CLAUDE.md`
```

## Steps

Ask only for what the current state lacks, in as few questions as possible, and don't narrate between them. A re-run with everything declared asks nothing and changes nothing.

1. **Languages.** Ask for the Conversation and the Content language, each as `Language (Region)`, such as `Spanish (Mexico)`. Structure is always English and is not asked.

2. **Atlassian.** Ask for the site, the Jira space and the Confluence space from what the Atlassian tools return; without them, ask in a plain message. Keep keys, never numeric IDs.
   - List Confluence spaces without a type filter (a team space can be `knowledge_base`, not `global`) and leave out personal ones (keys starting with `~`).
   - With a single site, use it and say so.
   - Ask for the Jira and the Confluence space with their keys as options, even when there is a single one, adding an option to type another key.

3. **Integration.** Ask how finished work reaches `develop`, with `merge` first and labeled `(Recommended)`, and `pull-request`. Ask it only when `.gemba/project/git.json` is missing.

4. **CLAUDE.md.** Make `CLAUDE.md` start with the template above, filled in. When `CLAUDE.md` already has a `# Gemba` block, update that block in place; when it has other content, insert the block above it with Edit, never retyping it; when it is missing, write it.

5. **Atlassian declaration.** Write `.gemba/project/atlassian.json` exactly in this shape:

   ```json
   {
     "site": "<site>.atlassian.net",
     "jira": { "project": "<KEY>" },
     "confluence": { "space": "<KEY>" }
   }
   ```

6. **Integration declaration.** Write `.gemba/project/git.json` exactly in this shape:

   ```json
   {
     "integration": "<merge or pull-request>"
   }
   ```

7. **Attribution.** In `.claude/settings.json`, set this key, keeping every other key, with two-space indentation and one key per line. Create the file when it is missing.

   ```json
   "attribution": {
     "commit": "",
     "pr": "",
     "sessionUrl": false
   }
   ```

8. **Worktrees.** Make `.gitignore` ignore the folder where worktrees live, so they are never tracked:
   - **Missing:** create it with the single line `.claude/worktrees/`.
   - **Without that line:** append it at the end, after a newline when the last line has none, keeping every other line.
   - **With that line:** change nothing.

9. **Git history,** last, so the initial commit holds what the steps above wrote.

   - **With history:** change nothing; report what is missing among `main`, `origin`, `develop` and their upstreams, each with the command that adds it, and name the files the steps above changed, which stay uncommitted.
   - **Without history:**
     1. Ask for the URL of an empty remote repository in a plain message. Check it with `git ls-remote <url>`: stop if it fails or lists any ref.
     2. Run `git init -b main` when `.git` is missing, else `git symbolic-ref HEAD refs/heads/main`, and show `git status --short --untracked-files=all` as the files the initial commit will hold.
     3. Run `git add -A`, `git commit -m "initial commit"`, with no trailers, and `git remote add origin <url>` (`git remote set-url origin <url>` when `origin` exists).
     4. Ask whether to push. Only on a yes, run `git push -u origin main`, `git switch -c develop` and `git push -u origin develop`.

10. **Report** one line per step: what changed, or that it was already right. Say that the changes apply from the next session. Reply in the Conversation language.
