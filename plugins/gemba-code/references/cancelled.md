# Cancellation comment

A work item is cancelled only when the person decides it, in the request or after a stop. The comment says why, what shows it and what replaces it, with its labels in English and the rest in the `Content:` language:

```markdown
### Cancelled

* Reason: <why the person decided to cancel it>
* Found: <what shows it: the `ran:` command and its output, or the `read:` source>
* Replaced by: <the key of the work item that replaces it, or the item saying there is none: `Ninguno.` in Spanish>
```

The comment reaches Jira as ADF, so the key of `Replaced by` becomes a link to the issue; the work item is then marked with the transition whose destination (`to.name`) is Cancelled, picked by destination, never by id. Before the Implement mark, cancelling marks nothing else and creates no branch: the comment and the Cancelled mark are its only writes. After the mark, the branch stays as it is.
