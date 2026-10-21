# Gemba Code

## Work items

Types: `bug` (incorrect behavior of something that exists), `epic` (a goal that groups the others), `spike` (time-boxed research that delivers knowledge, not code) and `story` (a deliverable feature).

## Work cycle

Every type goes through its own `<type>-start`, `<type>-implement`, `<type>-review` and `<type>-close` skills, in that order; each skill's own description says what it does for that type. Only `story` and `bug` merge a branch into `develop`; an epic's cycle touches no branch, and a spike's branch is deleted, never merged.

## Branches

- Work branches start from an up-to-date `develop` (`git pull --ff-only`) and merge back into it with `--no-ff`, then are deleted; a spike branch is deleted without a merge.
- Format: `<work-item-type>/<KEY>/<summary>`, for example `story/ABC-1/let-customers-download-their-invoices`, with `<work-item-type>` one of `bug`, `spike` or `story` and `<summary>` the work item's summary in lowercase kebab-case.
- Merge messages name the target branch: `Merge branch 'story/ABC-1/let-customers-download-their-invoices' into develop`.
- A pushed branch is never rebased, amended or force-pushed.

## Commits

- A single line, in English, with no body, footer or trailers. The description is lowercase except a proper name (brand, company or product) or an acronym, which keep their canonical capitalization (`Jira`, `CI`, `JSON`); an identifier (branch, scope, executable or file) is written as it is in the code (`gemba-code`, `CLAUDE.md`).
- Format: `<type>(<scope>): <description>`, with a type among `feat`, `fix`, `test`, `refactor`, `docs` and `chore`, a scope that names the work item's component, or the file itself when there is none (`docs(readme)`), and an imperative description with no final period that never repeats the branch name. Example: `feat(billing): add invoice export`.
- Commits are split by what was done.
