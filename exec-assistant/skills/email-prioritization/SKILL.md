---
name: email-prioritization
description: Classify inbox threads with Gmail priority labels (p1–p5) based on sender and action requirements.
allowed-tools: mcp__personal-context__list_contacts
---

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

1. Resolve the **executive sender list** (email addresses that always receive p1):

   a. **Try personal-context MCP first:** Call `mcp__personal-context__list_contacts`. Collect all contacts whose record identifies them as an executive (e.g. `team: Executive`, `role: executive`, or `is_executive: true` — use whatever field is present).

   b. **CLAUDE.md fallback:** If the MCP is unavailable or returns no results, read the project `CLAUDE.md` and look for an `## Email Prioritization` or `## Executives` config block. Use the email addresses listed there. Example block format:
      ```
      ## Email Prioritization
      executives:
        - ceo@example.com
        - cto@example.com
      ```

   c. If neither source is available, proceed without an executive sender list (no addresses will match p1 on sender alone).

2. Search Gmail inbox threads using the query `in:inbox AND NOT label:newsletters` with `pageSize: 20`.

3. List all Gmail labels and identify the IDs for `Priority/p1`, `Priority/p2`, `Priority/p3`, `Priority/p4`, and `Priority/p5`.

4. For each thread, find the most recent message and determine exactly one priority label using the rules in **Priority Levels** below (when multiple rules match, choose the highest priority — lowest number).

5. Call `label_message` with the message ID of the most recent message and the label ID for the assigned priority.

   - Apply all labels — do not skip threads that may already be labeled.
   - If a thread already has a priority label, only apply a new one if the new priority is higher (p1 > p2 > p3 > p4 > p5). Each thread must have exactly one priority label.

6. Do not output a summary. Just apply the labels and finish.

## Priority Levels

| Label | Rules (first match wins at lowest number) |
|-------|-------------------------------------------|
| p1 | Sender is in the executive sender list (resolved from personal contacts); OR the email requires an immediate action or decision that must be handled today |
| p2 | Requires any action or decision from the recipient; OR has medium time-sensitivity (respond this week); OR is a project or status update requiring a response |
| p3 | Routine communication or general update; OR sender's email domain matches the organization domain |
| p4 | Automated tool notifications, company-wide announcements, event registration confirmations |
| p5 | Newsletters, cold sales outreach, product marketing messages |

### Floor Rules

These override content-based classification — apply regardless of topic:

- Any organizational domain sender → at least p3
- Any email requiring action or decision → at least p2
- Any executive sender (from personal contacts) → always p1

## Integration

The chief-of-staff `/start-day` and `/finish-day` skills read p1/p2 emails directly from Gmail — this skill ensures those labels are current before the briefing runs.
