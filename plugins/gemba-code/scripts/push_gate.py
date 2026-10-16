#!/usr/bin/env python3
"""Gates `git push` before the Bash tool runs it.

Usage: a PreToolUse hook; it reads the hook input from stdin.

Prints a PreToolUse decision: `deny` for a forced push (`--force`, `--force-with-lease`,
`-f`, a `+refspec`) and `ask` for any other push. It prints nothing for a command that
pushes nothing. A push is a `git` command, with any path, env assignments and global
options before it, whose subcommand is `push`, in any segment of the command line.
Wrappers (`sh -c`, `xargs`, `env`) and git aliases are out of scope.
"""

import json
import os
import re
import shlex
import sys

# Global options of git that take their value as the next word.
WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
SEPARATORS = set("&;|()<>")
# Words of the shell that can come before a command.
KEYWORDS = {"if", "then", "elif", "else", "while", "until", "do", "time", "!", "{"}


def segments(command):
    """Splits a command line into the word lists of its simple commands."""
    lexer = shlex.shlex(command.replace("\n", ";").replace("`", ";"), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    current = []
    for word in lexer:
        if set(word) <= SEPARATORS:
            yield current
            current = []
        else:
            current.append(word)
    yield current


def push_arguments(words):
    """Returns the arguments after `push` when the words are a git push, else None."""
    words = list(words)
    while words and (words[0] in KEYWORDS or re.fullmatch(r"[A-Za-z_]\w*=.*", words[0])):
        words.pop(0)
    if not words or os.path.basename(words[0]) != "git":
        return None
    rest = words[1:]
    while rest and rest[0].startswith("-"):
        rest = rest[2:] if rest[0] in WITH_VALUE else rest[1:]
    return rest[1:] if rest and rest[0] == "push" else None


def forced(arguments):
    return any(
        argument.startswith("--force")
        or (argument.startswith("-") and not argument.startswith("--") and "f" in argument)
        or argument.startswith("+")
        for argument in arguments
    )


def decide(command):
    """Returns ("ask" | "deny", reason) for a command that pushes, else None."""
    try:
        pushes = [a for a in map(push_arguments, segments(command)) if a is not None]
    except ValueError:  # unbalanced quotes: read the words as they are written
        words = command.split()
        pushes = [words[words.index("push") + 1:]] if "git" in map(os.path.basename, words) and "push" in words else []
    if not pushes:
        return None
    if any(forced(arguments) for arguments in pushes):
        return "deny", "A forced git push can overwrite remote history, so Gemba Code does not allow it."
    return "ask", "Every git push waits for the person's explicit yes: state the branch and the commits it sends."


def main():
    command = (json.load(sys.stdin).get("tool_input") or {}).get("command", "")
    decision = decide(command) if isinstance(command, str) else None
    if decision:
        verdict, reason = decision
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict,
            "permissionDecisionReason": reason,
        }}))


if __name__ == "__main__":
    main()
