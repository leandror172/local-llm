---
id: cls-03-bug-severity
domain: classification
difficulty: medium
timeout: 120
description: Bug severity classification from a bug report
---

Classify the severity of the following bug report.

Severity levels:
- critical: system down, data loss, security breach, or affects all users
- high: major feature broken, significant user impact, no workaround
- medium: feature partially broken, workaround exists
- low: cosmetic issue, minor inconvenience, edge case

Bug report: "On the checkout page, if a user applies a discount code and then changes their shipping address, the discount code is silently removed and the user is charged full price. They only notice when they receive the invoice. This happens consistently on Chrome and Safari."

Respond with JSON: {"category": "<severity>", "confidence": <0.0-1.0>, "reasoning": "<explanation citing specific aspects of the bug>"}
