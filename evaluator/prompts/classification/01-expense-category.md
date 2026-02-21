---
id: cls-01-expense-category
domain: classification
difficulty: easy
timeout: 120
description: Classify a transaction into an expense category
---

Classify the following transaction description into exactly one expense category.

Categories: food, transport, housing, utilities, healthcare, entertainment, shopping, travel, education, other

Transaction: "Uber Eats order - Thai Palace Restaurant $34.50"

Respond with a JSON object: {"category": "<category>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}
