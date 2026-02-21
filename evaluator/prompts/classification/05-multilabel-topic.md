---
id: cls-05-multilabel-topic
domain: classification
difficulty: hard
timeout: 120
description: Primary topic classification of a technical article
---

Classify the PRIMARY topic of the following technical article excerpt into exactly one category.

Categories: machine-learning, databases, distributed-systems, security, frontend, backend, devops, mobile, data-engineering, other

Article excerpt:
"Raft is a consensus algorithm designed as an alternative to Paxos. It separates key elements of consensus, such as leader election, log replication, and safety, and enforces a stronger degree of coherency to reduce the number of states that must be considered. Raft also includes a new mechanism for cluster membership changes using joint consensus, where two different configurations overlap during transitions. This allows the cluster to continue operating normally during configuration changes."

Respond with JSON: {"category": "<primary_topic>", "confidence": <0.0-1.0>, "reasoning": "<one sentence explaining why this is the primary topic>"}
