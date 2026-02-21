# RFC Process

For larger changes or new features, ChattyCommander uses a lightweight RFC (Request for Comments) process.

## When to Write an RFC

Write an RFC when your change:

- Adds a new major feature or integration
- Changes a public API or configuration schema
- Affects multiple modules in a breaking way
- Requires architectural decisions

For small fixes, tests, or doc updates — just open a PR directly.

## RFC Lifecycle

```
[Draft] → [Open for Comment] → [Accepted] → [Implemented] → [Closed]
                 ↓
            [Withdrawn]
```

1. **Draft**: Author creates a GitHub issue using the RFC template
2. **Open**: Issue is labeled `rfc` and open for community comment (2 week minimum)
3. **Accepted**: Maintainer approves — author creates the PR
4. **Implemented**: PR merged, RFC issue closed with link to PR

## RFC Issue Template

```markdown
## Summary
One-paragraph description of the feature/change.

## Motivation
Why is this needed? What problem does it solve?

## Detailed Design
How will this be implemented? Include API changes, config schema additions, etc.

## Drawbacks
Any downsides or trade-offs?

## Alternatives Considered
What else was considered and why was it rejected?

## Unresolved Questions
What needs to be figured out during implementation?
```

## Acceptance Criteria

An RFC is accepted when:
- It has received at least 7 days of open review
- No outstanding blocking objections exist
- A maintainer has given explicit approval (👍 on the issue)

## Past RFCs

See GitHub Issues labeled [`rfc`](https://github.com/matthewhand/chatty-commander/issues?q=label%3Arfc).
