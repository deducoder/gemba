# Cause in the tests

The cause of a bug is in the tests when every `read:` line of its Root cause points to a test of the project, not to the product. Then the fixed test is the whole fix: it passes on the product as it is, the branch holds only its `test` commit, with no `fix` commit, and the Neighboring inputs keep their behavior because the product does not change.

A fixed test cannot fail without a fix that does not exist, so it shows instead that it detects the defect: it fails against a change to the product, near the code the test checks, run in a worktree of develop. The Done when names that change in one criterion, in the `Content:` language: "With <the change to the product>, <command that runs the fixed test> fails".
