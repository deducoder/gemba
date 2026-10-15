---
name: session-start
description: Opens a block of work from the latest handoff in .gemba/sessions/, checked against the current state of the project. Use when the user starts or resumes a session, asks where they left off or what is next, or right after /clear in a project with handoffs. Writes nothing and starts no work before the user confirms the focus.
disallowed-tools:
  - Write
  - Edit
  - NotebookEdit
---

# Session start

Project root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`

Latest handoff: !`ls -1t "${CLAUDE_PROJECT_DIR}"/.gemba/sessions/*.md 2>/dev/null | head -n 1 | grep . || echo "(none)"`

Branch: !`git branch --show-current 2>/dev/null | grep . || git rev-parse --short HEAD 2>/dev/null || echo "(none)"`

Uncommitted changes:

```
!`git status --short 2>/dev/null | grep . || echo "(none)"`
```

Recent commits:

```
!`git log --oneline -5 2>/dev/null | grep . || echo "(none)"`
```

1. **Find the handoff.** When the latest handoff above is none, look for the newest `.gemba/sessions/*.md` at the project root above and use it. When there is none there either, say so, ask the user what to work on and stop.

2. **Read the latest handoff.**

3. **Check its Next against the branch, the uncommitted changes, the recent commits and the files it names:** done, partly done, no longer applies, or still valid. Where they disagree, the project wins.

4. **Raise every Open question first:** it may change what is worth doing.

5. **Propose one focus and why,** and wait for the user to confirm it before starting any work.

6. **Reply** in the `Conversation:` language of the `## Language` section in `CLAUDE.md`, or in the conversation's language when there is none.
