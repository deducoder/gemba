# Gemba Code

## Work items

Types: `bug` (incorrect behavior of something that exists), `epic` (a goal that groups the others), `spike` (time-boxed research that delivers knowledge, not code) and `story` (a deliverable feature).

## Branches

- Work branches start from an up-to-date `develop` (`git pull --ff-only`) and merge back into it with `--no-ff`, then are deleted; a spike branch is deleted without a merge.
- Format: `<work-item-type>/<KEY>/<summary>`, for example `story/ABC-1/let-customers-download-their-invoices`, with `<work-item-type>` one of `bug`, `spike` or `story` and `<summary>` the work item's summary in lowercase kebab-case.
- Merge messages name the target branch: `Merge branch 'story/ABC-1/let-customers-download-their-invoices' into develop`.
- A pushed branch is never rebased, amended or force-pushed.

## Commits

- A single line, in English, lowercase except canonical names (`CLAUDE.md`), with no body, footer or trailers.
- Format: `<type>(<scope>): <description>`, with a type among `feat`, `fix`, `test`, `refactor`, `docs` and `chore`, a scope that names the work item's component, or the file itself when there is none (`docs(readme)`), and an imperative description with no final period that never repeats the branch name. Example: `feat(billing): add invoice export`.
- Commits are split by what was done.
