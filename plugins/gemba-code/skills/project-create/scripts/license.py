#!/usr/bin/env python3
"""Reads the project's public visibility from its GitHub origin, or downloads the text of
a license to propose.

Usage:
    python3 license.py
    python3 license.py mit
    python3 license.py apache-2.0

Without an argument, reads `git remote -v`, finds the `origin` remote and, when it is a
`github.com` remote (`https://github.com/<owner>/<repo>`, `git@github.com:<owner>/<repo>`,
either with or without a trailing `.git`), asks the GitHub API for it with no credentials.
Prints {"owner": ..., "repo": ..., "public": true} when the API answers 200, or
{"public": false} for any other remote, response or error. Never raises: a network failure
here means "do not propose", not a crash.

With `mit`, downloads the MIT license template from choosealicense.com and prints only its
body, the text after the template's front matter, with the `[year]` and `[fullname]`
placeholders of https://raw.githubusercontent.com/github/choosealicense.com/gh-pages/_licenses/mit.txt.
With `apache-2.0`, downloads the full text of
https://www.apache.org/licenses/LICENSE-2.0.txt as is.

Either one prints the license text to stdout and exits 0. A failed download prints why to
stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

ORIGIN = re.compile(r"^origin\s+(\S+)\s+\(fetch\)")
GITHUB_HTTPS = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$")
GITHUB_SSH = re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$")
MIT_URL = "https://raw.githubusercontent.com/github/choosealicense.com/gh-pages/_licenses/mit.txt"
APACHE_URL = "https://www.apache.org/licenses/LICENSE-2.0.txt"


def origin_url():
    """Returns the `origin` remote's fetch URL from `git remote -v`, or None without one."""
    output = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, check=False).stdout
    for line in output.splitlines():
        match = ORIGIN.match(line)
        if match:
            return match.group(1)
    return None


def owner_and_repo(url):
    """Returns the (owner, repo) of a github.com remote URL, https or SSH, or None."""
    for pattern in (GITHUB_HTTPS, GITHUB_SSH):
        match = pattern.match(url)
        if match:
            return match.group(1), match.group(2)
    return None


def is_public(owner, repo):
    """Asks the GitHub API, with no credentials, whether owner/repo answers 200."""
    try:
        with urllib.request.urlopen(f"https://api.github.com/repos/{owner}/{repo}", timeout=10) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


def visibility():
    url = origin_url()
    pair = owner_and_repo(url) if url else None
    if not pair:
        return {"public": False}
    owner, repo = pair
    return {"owner": owner, "repo": repo, "public": is_public(owner, repo)}


def mit_body(text):
    """Returns the text of a choosealicense.com template after its front matter."""
    return text.split("---\n", 2)[2].strip() + "\n"


def download(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def main():
    if len(sys.argv) == 1:
        print(json.dumps(visibility()))
        return 0
    which = sys.argv[1]
    if which not in ("mit", "apache-2.0"):
        print(f"license: {which} is not mit or apache-2.0", file=sys.stderr)
        return 1
    try:
        text = download(MIT_URL if which == "mit" else APACHE_URL)
    except (urllib.error.URLError, OSError) as error:
        print(f"license: could not download {which}: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(mit_body(text) if which == "mit" else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
