---
name: setup
description: Prepares a project for Gemba. Declares Gemba and the languages in CLAUDE.md, the Atlassian site, Jira project and Confluence space in .gemba/project/atlassian.json, turns off commit and PR attribution, and creates the initial git history. Safe to re-run.
disable-model-invocation: true
---

# Setup

## Current state

CLAUDE.md:

```
!`cat CLAUDE.md 2>/dev/null || echo "(missing)"`
```

.gemba/project/atlassian.json:

```
!`cat .gemba/project/atlassian.json 2>/dev/null || echo "(missing)"`
```

.claude/settings.json:

```
!`cat .claude/settings.json 2>/dev/null || echo "(missing)"`
```

Git:

```
!`git log --oneline -1 2>/dev/null && git branch -vv && git remote -v || echo "(no history)"`
```

## Steps

Ask only for what the current state lacks, in as few questions as possible, and don't narrate between them. A re-run with everything declared asks nothing and changes nothing.

1. **Languages.** Ask for the Conversation and the Content language, each as `Language (Region)`, such as `Spanish (Mexico)`. Structure is always English and is not asked.

2. **Atlassian.** Ask for the site, the Jira space and the Confluence space from what the Atlassian tools return; without them, ask in a plain message. Keep keys, never numeric IDs.
   - List Confluence spaces without a type filter (a team space can be `knowledge_base`, not `global`) and leave out personal ones (keys starting with `~`).
   - With a single site, use it and say so.
   - Ask for the Jira and the Confluence space with their keys as options, even when there is a single one, adding an option to type another key.

3. **CLAUDE.md.** Read the template at `${CLAUDE_SKILL_DIR}/assets/CLAUDE.md` and make `CLAUDE.md` start with it, filled in. When `CLAUDE.md` already has a `# Gemba` block, update that block in place; when it has other content, insert the block above it with Edit, never retyping it; when it is missing, write it.

4. **Atlassian declaration.** Write `.gemba/project/atlassian.json` exactly in this shape:

   ```json
   {
     "site": "<site>.atlassian.net",
     "jira": { "project": "<KEY>" },
     "confluence": { "space": "<KEY>" }
   }
   ```

5. **Attribution.** In `.claude/settings.json`, set this key, keeping every other key, with two-space indentation and one key per line. Create the file when it is missing.

   ```json
   "attribution": {
     "commit": "",
     "pr": "",
     "sessionUrl": false
   }
   ```

6. **Git history,** last, so the initial commit holds what the steps above wrote.

   - **With history:** change nothing; report what is missing among `main`, `origin`, `develop` and their upstreams, each with the command that adds it, and name the files the steps above changed, which stay uncommitted.
   - **Without history:**
     1. Ask for the URL of an empty remote repository in a plain message. Check it with `git ls-remote <url>`: stop if it fails or lists any ref.
     2. Run `git init -b main` when `.git` is missing, else `git symbolic-ref HEAD refs/heads/main`, and show `git status --short --untracked-files=all` as the files the initial commit will hold.
     3. Run `git add -A`, `git commit -m "initial commit"`, with no trailers, and `git remote add origin <url>` (`git remote set-url origin <url>` when `origin` exists).
     4. Ask whether to push. Only on a yes, run `git push -u origin main`, `git switch -c develop` and `git push -u origin develop`.

7. **Report** one line per step: what changed, or that it was already right. Say that the changes apply from the next session. Reply in the Conversation language.
