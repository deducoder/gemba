#!/bin/bash
# Builds the project the spike-start cases observe: the story-start invoice project,
# whose invoices live in a list in invoices.py and which says nothing about any
# billing API, so a question about one is not answered by the project.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-start/project.sh"
