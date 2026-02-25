---
id: cls-02-sentiment
domain: classification
difficulty: easy
timeout: 120
description: Sentiment classification with confidence score
---

Classify the sentiment of the following product review.

Categories: positive, negative, neutral, mixed

Review: "The battery life is amazing and the camera is great, but the build quality feels cheap and it gets hot during gaming sessions. Overall it's decent for the price."

Respond with a JSON object: {"category": "<category>", "confidence": <0.0-1.0>, "reasoning": "<one sentence explaining the classification>"}
