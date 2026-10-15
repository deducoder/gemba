# Gemba

**Gemba (現場)** is an agentic development framework for Claude Code, built on *genchi genbutsu* (現地現物): go to the source, observe the facts, then act. Its name comes from Toyota's Lean, where *gemba* is the real place where value is created and *genchi genbutsu* is its guiding principle: go and see the real thing for yourself before deciding.

For an agent, the gemba is the code, the running system and the work item; not its memory or its assumptions. Gemba guides the agent to observe that real source before proposing a change, to back every claim with evidence, and to stop when what it observes contradicts the plan.

## Plugins

This repository is a Claude Code marketplace named `gemba`.

| Plugin | What it provides |
| --- | --- |
| `gemba` | Values, method, communication and language rules, injected into every session, plus the setup and session skills |
| `gemba-code` | Gemba applied to code: the work cycle of bugs, epics, spikes and stories, and the git rules |

## Quick start

**Requirements:** Linux or WSL, with Claude Code, `git` and `python3` on your `PATH`.

Gemba is enabled per project, never at user scope. From the project root, add the marketplace and install the plugin, both at project scope, so they are declared in the project's `.claude/settings.json`:

```bash
claude plugin marketplace add deducoder/gemba --scope project
claude plugin install gemba@gemba --scope project
```

In a code project, install `gemba-code` to add the work item, branch and commit rules. It depends on `gemba`, so installing it installs `gemba` too:

```bash
claude plugin install gemba-code@gemba --scope project
```

For a project without commits, first create an empty remote repository, such as one on GitHub. Then open Claude Code in the project and run `/gemba:setup` to declare Gemba and the project's languages in `CLAUDE.md`, and the Atlassian site, Jira space and Confluence space in `.gemba/project/atlassian.json`, and to turn off commit and PR attribution in `.claude/settings.json`. Without commits, setup ends by creating the history: `initial commit` on `main` with everything not ignored, `origin`, and, once you approve the push, `develop`. With commits, it only reports what the history lacks and the files it left uncommitted, so commit `.claude/settings.json`, `CLAUDE.md` and `.gemba/project/atlassian.json` yourself.

To pause a block of work, run `/gemba:session-close`: it leaves a handoff in `.gemba/sessions/`, kept out of git. After `/clear` or in a new session, run `/gemba:session-start` to resume from it.

Auto-update is off by default for third-party marketplaces. To receive new versions, turn it on in `/plugin` > Marketplaces > Enable auto-update, or update manually with `claude plugin update gemba@gemba --scope project` (and `gemba-code@gemba` when installed) and restart Claude Code.

## Development

```bash
claude --plugin-dir ./plugins/gemba               # load the plugin in a session
claude plugin validate . --strict                 # validate the marketplace
claude plugin validate plugins/gemba --strict     # validate the plugin
python3 -m unittest discover tests                # run the tests
```

Inside the session, `/reload-plugins` applies changes without restarting.

## License

[Apache License 2.0](LICENSE). If you redistribute Gemba or a derivative work, keep the copyright notice and the [NOTICE](NOTICE) file with the attribution to the author.

Copyright 2026 Daniel Efraín Domínguez Urbina ([deducoder](https://github.com/deducoder)).
