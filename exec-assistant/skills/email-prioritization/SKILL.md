# Email Prioritization

Label incoming Gmail messages with priority levels (p1–p5) and structured labels so the chief-of-staff and finish-day wrap-up can surface what needs attention.

## Usage

```
/exec-assistant:email-prioritization
/exec-assistant:email-prioritization --max-messages 50
```

## Arguments

- `--max-messages` — Maximum number of unread messages to process (default: 25)

## Behavior

<!-- Paste your existing email prioritization logic here -->
<!-- The skill should: -->
<!-- 1. Fetch unread/unlabeled messages from Gmail -->
<!-- 2. Evaluate each message against priority criteria -->
<!-- 3. Apply Gmail labels (p1/p2/p3/p4/p5) -->
<!-- 4. Return a summary of what was labeled -->

## Priority Levels

| Label | Criteria |
|-------|----------|
| p1 | Requires your response today; from exec/board/key stakeholder |
| p2 | Requires your response this week; time-sensitive but not urgent |
| p3 | FYI or needs response when convenient |
| p4 | Newsletter, digest, low-signal; archive after reading |
| p5 | Automated/spam; can be deleted |

## Integration

The chief-of-staff `/start-day` and `/finish-day` skills read p1/p2 emails directly from Gmail — this skill ensures those labels are current before the briefing runs.
