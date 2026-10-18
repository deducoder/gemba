---
name: version-close
description: Releases a product version whose work items are finished. Checks that every work item of its fix version is Done or Cancelled, runs /security-review on the changes of the version, merges develop into main with --no-ff, tags the version and pushes main, the tag and develop with the person's yes, releases the fix version in Jira with today's date, marks its page Released and moves its entry from Now to Released in the Roadmap. Stops, writing nothing, without a version Planned or In progress in Now, with a work item still open or with a finding of the security review. Use when the user asks to close, release or ship a product version planned with version-start. It does not write what the version taught.
argument-hint: "[version in Now, like <Product> vX.Y.Z]"
disable-model-invocation: true
allowed-tools:
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/release.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/released.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py *)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py *)
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

Until the push of step 7 this skill only reads and works locally: it writes nothing in Jira or Confluence and sends nothing to the remote. Its writes are the release in git, the release of the fix version, the stamp of the version page and the `Now` and `Released` sections of `Roadmap`. It does not write `Learned`, nor change `Requirements`. The `site` in `atlassian.json` above is the `cloudId` of every Atlassian call, `jira.project` the project and `confluence.space` the space of the pages.

1. **Check the project.** When `atlassian.json` above is `(missing)`, or `CLAUDE.md` above has no `# Gemba` block, reply that the project needs `/gemba:setup` first and stop, without calling Atlassian.

2. **Find the version.** Read the space of `atlassian.json` with `getConfluenceSpaces` (its `id` and `homepageId`) and the children of its home with `getConfluencePageDescendants` and `depth: 1`, following its `cursor` until the last page, and then the children of the page titled `Vision` the same way: `Roadmap` is one of them. Without `Vision` or without `Roadmap`, reply that the product needs `/gemba-code:project-create` first and stop. Read `Roadmap` with `getConfluencePage` and `contentFormat: "adf"`. The versions in progress are the entries of `Now` whose lozenge is `Planned` or `In progress`: each one carries its name `<Product> vX.Y.Z`, the link to its page, its goal and its `Target`. Without any, reply that no version is in progress in `Now` and stop, writing nothing. The version is the one the argument names; with one alone and no argument, that one; with several and no argument, ask which.

3. **Check the fix version.** Find the id of the issue type Epic with `getJiraProjectIssueTypesMetadata` and read the `allowedValues` of `fixVersions` with `getJiraIssueTypeMetaWithFields` and `requiredFieldsOnly: false`. The fix version named as the version must be there; take its `id`. When it is missing, say that it is missing or archived and stop, writing nothing. When it is already released while the version is still in `Now`, an earlier run stopped after step 8: say so and go on from step 9.

4. **Check the work items.** Read with `searchJiraIssuesUsingJql` the work items of the version not finished (`project = <jira.project> AND fixVersion = "<the version>" AND status not in (Done, Cancelled)`, every page, with their `summary`, `issuetype` and `status`). With any, stop, writing nothing, and name each one with its key, type, Summary and status.

5. **Review the security.** When `git status --porcelain --untracked-files=no` lists changes, stop: name them and say to commit or discard them first. Otherwise bring `develop` up to date (`git switch develop` and `git pull --ff-only`) and invoke `/security-review` with the Skill tool, from `develop`. It reviews the diff against `origin/HEAD`, and the changes of the version are what `develop` has and `origin/main` lacks: when `git rev-parse --abbrev-ref origin/HEAD` is another branch, run `git remote set-head origin main` before the review.

   The review is a step of this skill and its report is not the reply: once it reports, go on in the same turn, with findings or without. First, when you moved `origin/HEAD`, put it back with `git remote set-head origin <that branch>`. Then, with a finding, stop without releasing: name each finding with its file and its severity, suggest declaring it with `/gemba-code:bug-start` and running this skill again once it is fixed. Without findings, go on to step 6.

6. **Release in git** with this command, run alone and exactly in this form, with the number of the version:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/release.py v<X.Y.Z>
   ```

   It prints the tag, then on a second line `released` when it merged `develop` into `main` with `--no-ff` and tagged the merge, or `already released` when an earlier run did, and then the commits the push of `main` sends. It leaves the project on `develop`, level with `main`. When it refuses, relay its reason and stop: nothing is pushed or released.

7. **Push,** in this order, each one as a command of its own that the person approves: `git push origin main`, `git push origin refs/tags/v<X.Y.Z>` and `git push origin develop`. Before the first, say the tag and the commits step 6 listed. When a push fails or the person declines it, stop: say what was pushed, and nothing is released in Jira.

8. **Release the fix version** with `manageJiraProjectVersion`, `action: "release"`, the `id` of step 3 as `versionId` and today as `releaseDate` (`YYYY-MM-DD`). When it returns an error, stop: relay Jira's reason and say that git is already released and pushed.

9. **Mark the version page Released.** Read the page of the link of step 2 with `getConfluencePage` and `contentFormat: "adf"`, and run, alone and exactly in this form, with its body and today:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/released.py <<'PAGE'
   {"page": <the published body>, "day": "<YYYY-MM-DD>"}
   PAGE
   ```

   Update the page with `updateConfluencePage`, its `id` as `pageId`, its title and the document it printed as its `body` (`contentFormat: "adf"`).

10. **Move the entry to Released.** Write the draft of `Roadmap`, whole, from the page as published, in the `Content:` language of the `## Language` section in `CLAUDE.md`, or the conversation's language when there is none, the text it already has kept as it is: `Now` without the version, or one paragraph saying no version is in progress when it was the only one, and `Released` with `* [<the version>](<the link to its page>) [Released] <goal> Target: <the Target>` first, before the versions it already lists, or alone when it was a paragraph. Check it, alone and exactly in this form, fixing each problem it names until it passes:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py <<'ROADMAP'
    <the roadmap draft>
    ROADMAP
    ```

    Merge it, alone and exactly in this form, with the published body and the body the script printed, and update `Roadmap` with `updateConfluencePage` as step 9 does, with the document the merge printed:

    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge.py <<'MERGE'
    {"live": <the published body>, "new": <the body the script printed>, "replace": ["Now", "Released"]}
    MERGE
    ```

    A live doc saves late: read each of the two pages until it has the change, up to three times, and retry the update once when it still does not; then say which page did not save. When an update fails, stop and say what was written and what was not.

11. **Reply** with the tag and its merge commit, the fix version released and its date, and the links to the version page and `Roadmap`. Suggest `/gemba-code:version-start` for the next version. This skill writes no worklog.
