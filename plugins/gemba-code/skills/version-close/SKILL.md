---
name: version-close
description: Releases a product version whose work items are finished. Checks that every work item of its fix version is Done or Cancelled, runs /security-review on the changes of the version, merges develop into main with --no-ff, tags the version and pushes main, the tag and develop with the person's yes, releases the fix version in Jira with today's date, marks its page Released and moves its entry from Now to Released in the Roadmap. Then brings back what the version taught, only what the person accepts: Learned on its page, its requirements whose work items were all cancelled back to Unassigned, its answered questions and its new requirements in Requirements. Stops, writing nothing, without a version Planned or In progress in Now, with a work item still open or with a finding of the security review, and brings back nothing before the version is released. Use when the user asks to close, release or ship a product version planned with version-start, or to bring back what a released version taught.
argument-hint: "[version in Now, like <Product> vX.Y.Z]"
disable-model-invocation: true
allowed-tools:
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/release.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/released.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/learned.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py *)
---

# Version close

.gemba/project/atlassian.json:

```
!`cat "${CLAUDE_PROJECT_DIR}/.gemba/project/atlassian.json" 2>/dev/null || echo "(missing)"`
```

CLAUDE.md:

```
!`cat "${CLAUDE_PROJECT_DIR}/CLAUDE.md" 2>/dev/null || echo "(missing)"`
```

Until the push of step 7 this skill only reads and works locally: it writes nothing in Jira or Confluence and sends nothing to the remote. Its writes are the release in git, the release of the fix version, the stamp of the version page, the `Now` and `Released` sections of `Roadmap`, and then, only with what the person accepted, the `Learned` section of the version page and the sections of `Requirements` that change. It brings back what the version taught only once the version is released: when it stops before the end of step 10, it says that what the version taught comes back once the version is released, and writes neither `Learned` nor `Requirements`. The `site` in `atlassian.json` above is the `cloudId` of every Atlassian call, `jira.project` the project and `confluence.space` the space of the pages. Resolve the operations this skill names below with:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/atlassian_op.py getConfluencePage updateConfluencePage getConfluencePageDescendants getConfluenceSpaces getJiraProjectIssueTypesMetadata getJiraIssueTypeMetaWithFields searchJiraIssuesUsingJql manageJiraProjectVersion setConfluenceContentStatus
```

!`cat ${CLAUDE_PLUGIN_ROOT}/references/atlassian-operation.md`

1. **Check the project.** When `atlassian.json` above is `(missing)`, or `CLAUDE.md` above has no `# Gemba` block, reply that the project needs `/gemba:setup` first and stop, without calling Atlassian.

2. **Find the version.** Read the space of `atlassian.json` with `getConfluenceSpaces` (its `id` and `homepageId`) and the children of its home with `getConfluencePageDescendants` and `depth: 1`, following its `cursor` until the last page, and then the children of the page titled `Vision` the same way: `Roadmap` is one of them. Without `Vision` or without `Roadmap`, reply that the product needs `/gemba-code:project-create` first and stop. Read `Roadmap` with `getConfluencePage`, `contentFormat: "html"` and `detail: "full"` (its `snapshotToken` is needed to update it later). The versions in progress are the entries of `Now` whose lozenge is `Planned` or `In progress`: each one carries its name `<Product> vX.Y.Z`, the link to its page, its goal and its `Target`. A version in `Released` may still have to bring back what it taught, because a close stopped before or the person asks again: when the argument names it, go on from step 11 with it. Without any version in progress, and without the argument naming one of those, reply that no version is in progress in `Now` and stop, writing nothing. The version is the one the argument names; with one alone and no argument, that one; with several and no argument, ask which.

3. **Check the fix version.** Find the id of the issue type Epic with `getJiraProjectIssueTypesMetadata` and read the `allowedValues` of `fixVersions` with `getJiraIssueTypeMetaWithFields` and `requiredFieldsOnly: false`. The fix version named as the version must be there; take its `id`. When it is missing, say that it is missing or archived and stop, writing nothing. When it is already released while the version is still in `Now`, an earlier run stopped after step 8: say so and go on from step 9.

4. **Check the work items.** Read with `searchJiraIssuesUsingJql` the work items of the version not finished (`project = <jira.project> AND fixVersion = "<the version>" AND status not in (Done, Cancelled)`, every page, with their `summary`, `issuetype` and `status`). With any, stop, writing nothing, and name each one with its key, type, Summary and status.

5. **Review the security.** When `git status --porcelain --untracked-files=no` lists changes, stop: name them and say to commit or discard them first. Otherwise bring `develop` up to date (`git switch develop` and `git pull --ff-only`) and invoke `/security-review` with the Skill tool, from `develop`. It reviews the diff against `origin/HEAD`, and the changes of the version are what `develop` has and `origin/main` lacks: when `git rev-parse --abbrev-ref origin/HEAD` is another branch, run `git remote set-head origin main` before the review.

   The review is a step of this skill and its report is not the reply: once it reports, go on in the same turn, with findings or without. First, when you moved `origin/HEAD`, put it back with `git remote set-head origin <that branch>`. Then, with a finding, stop without releasing: name each finding with its file and its severity, suggest declaring it with `/gemba-code:bug-start` and running this skill again once it is fixed. Without findings, go on to step 6.

6. **Release in git** with this command, run alone and exactly in this form, with the number of the version:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/release.py v<X.Y.Z>
   ```

   It prints the tag, then on a second line `released` when it merged `develop` into `main` with `--no-ff` and tagged the merge, or `already released` when an earlier run did, and then the commits the push of `main` sends. It leaves the project on `develop`, level with `main`. When it refuses, relay its reason and stop: nothing is pushed or released.

7. **Push,** in this order, each one as a command of its own: `git push origin main`, `git push origin refs/tags/v<X.Y.Z>` and `git push origin develop`. Before the first, say the tag and the commits step 6 listed. When a push fails or is declined, stop: say what was pushed, and nothing is released in Jira.

8. **Release the fix version** with `manageJiraProjectVersion`, `action: "release"`, the `id` of step 3 as `versionId` and today as `releaseDate` (`YYYY-MM-DD`). When it returns an error, stop: relay Jira's reason and say that git is already released and pushed.

9. **Mark the version page Released.** Read the page of the link of step 2 with `getConfluencePage`, `contentFormat: "html"` and `detail: "full"`, and run, alone and exactly in this form, with its body and today:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/released.py <<'PAGE'
   {"page": <the published body>, "day": "<YYYY-MM-DD>"}
   PAGE
   ```

   Update the page with `updateConfluencePage`, its `id` as `pageId`, its `snapshotToken` from this step's read and the `edits` it printed. Then mark it `Released` with `setConfluenceContentStatus`, its `id` as `contentId`, `name: "Released"` and `color: "#57D9A3"`.

10. **Move the entry to Released.** Write the draft of `Roadmap`, whole, from the page as published, in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none, the text it already has kept as it is: `Now` without the version, or one paragraph saying no version is in progress when it was the only one, and `Released` with `* [<the version>](<the link to its page>) [Released] <goal> Target: <the Target>` first, before the versions it already lists, or alone when it was a paragraph. Check it, alone and exactly in this form, fixing each problem it names until it passes:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py <<'ROADMAP'
    <the roadmap draft>
    ROADMAP
    ```

    Merge it, alone and exactly in this form, with the published body and the body the script printed, and update `Roadmap` with `updateConfluencePage` as step 9 does, with its `snapshotToken` from step 2's read and the `edits` the merge printed:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py <<'MERGE'
    {"live": <the published body>, "new": <the body the script printed>, "replace": ["Now", "Released"]}
    MERGE
    ```

    A live doc saves late: read each of the two pages until it has the change, up to three times, and retry the update once when it still does not; then say which page did not save. When an update fails, stop and say what was written and what was not.

11. **Read what the version taught.** Read with `searchJiraIssuesUsingJql` every work item of the version (`project = <jira.project> AND fixVersion = "<the version>"`, every page, with their `summary`, `issuetype`, `status`, `description` and `comment`) and, in the same message, `Requirements`, a child of `Vision`, with `getConfluencePage`, `contentFormat: "html"` and `detail: "full"`.

12. **Propose what was learned.** From the drift and cancellation comments, the bugs found in the version and the questions it answered, propose lessons: each one plain sentence that the next version can act on, with `code` as its only mark. When the version page already has `Learned`, propose none and go on to step 13. Propose them in batches: one `AskUserQuestion` question with `multiSelect` per batch of up to four lessons. The person keeps what they accept and corrects with a note. When they accept at least one, read the version page again with `getConfluencePage`, `contentFormat: "html"` and `detail: "full"` and run, alone and exactly in this form, with its body and the accepted lessons, one `* ` bullet each:

    ```
    python3 ${CLAUDE_SKILL_DIR}/scripts/learned.py <<'PAGE'
    {"page": <the published body>, "draft": "<the lessons>"}
    PAGE
    ```

    It adds `Learned` at the end of the page and refuses a version that is not released yet. Right after step 9 a live doc may still show the old stamp: read the page again, up to three times, until it shows `Released`; when it still does not, say that what the version taught comes back once it is released, and stop. Update the page with `updateConfluencePage` as step 9 does, with this step's `snapshotToken` and the `edits` it printed, and read it until it has `Learned`, as step 10 does. When the person accepts none, the page does not change.

13. **Propose the requirements that go back.** For each requirement of the section of the version in `Requirements`, the work items of step 11 whose description cites it as `(R-nn)` cover it. When it has at least one and all of them are Cancelled, propose moving it back to `Unassigned`, with the keys of those work items, in batches as step 12 does. A requirement no work item cites stays in its version.

14. **Propose the answers and the new requirements.** Each `Open` question of `Assumptions and open questions` that the work items, the comments or the person answered or validated during the version: propose it with `Answer: <the answer>.` after its assumption and `[Answered]`, quoting where the answer comes from. Each new requirement that came out of the version, from its work items or from the person: propose it in `Unassigned` with the next ID above the highest of the page, withdrawn ones included, singular and verifiable, its `Type` and `Source: <the version>`. Propose both in batches as step 12 does.

15. **Write Requirements,** only when the person accepted something in steps 13 and 14. Write the draft of `Requirements`, whole, from the page as published, in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none, the text it already has kept as it is: the accepted requirements moved from the section of the version to `Unassigned`, in ascending order there, and the section of the version removed when it is left empty; the accepted answers; and the accepted new requirements at the end of `Unassigned`. Check it, alone and exactly in this form, with the IDs the published page has, fixing each problem it names until it passes:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.py --existing <the published IDs, comma separated> <<'REQUIREMENTS'
    <the requirements draft>
    REQUIREMENTS
    ```

    Merge it with `merge.py` as step 10 does, replacing only the sections that changed among the version, `Unassigned` and `Assumptions and open questions`, and update `Requirements` with `updateConfluencePage`, its `snapshotToken` from step 11's read and the `edits` the merge printed. Read `Requirements` until it has the change, as step 10 does.

16. **Reply** with the tag and its merge commit, the fix version released and its date, and the links to the version page and `Roadmap`; then the lessons written in `Learned`, the requirements moved back to `Unassigned`, the questions answered and the new requirements with their IDs, with the link to `Requirements`, or that the person accepted none. Suggest `/gemba-code:version-start` for the next version. This skill writes no worklog.
