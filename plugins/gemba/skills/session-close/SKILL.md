---
name: session-close
description: Closes a block of work and leaves a handoff in .gemba/sessions/ to resume it after /clear. Use when the user ends a block of work, stops, switches focus or is about to /clear. Writes only the handoff.
disable-model-invocation: true
allowed-tools:
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/handoff.py *)
disallowed-tools:
  - Write
  - Edit
  - NotebookEdit
---

# Session close

Title date: !`date "+%Y-%m-%d %H:%M"`

Uncommitted changes:

```
!`git status --short 2>/dev/null | grep . || echo "(none)"`
```

1. **Fill the template** at `${CLAUDE_SKILL_DIR}/assets/handoff.md` with what this block did, decided and left open, with the title date above. Keep its headings and labels in English, and write the content in the `Content:` language of the `## Language` section in `CLAUDE.md`, or in the conversation's language when there is none.

2. **Give every decision in Decided its why, and make Next one concrete action:** without the why, the decision gets reopened, and a list postpones the decision Next forces.

3. **Name in State the unsaved work and the uncommitted changes above.** When there are none, leave the section out.

4. **Save the handoff** with this command, run alone and exactly in this form. The `<slug>` is the block's focus in 2 or 3 words, in kebab-case.

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/handoff.py <slug> <<'HANDOFF'
   <the handoff>
   HANDOFF
   ```

   When it rejects the handoff, fix each problem it names and run it again.

5. **Reply** with the path it prints and suggest `/clear`.
