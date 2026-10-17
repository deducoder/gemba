#!/bin/bash
. "$(dirname "$0")/../../spike-review/project.sh"
git rm -q .gemba/project/atlassian.json && git commit -qm "drop the atlassian config"
