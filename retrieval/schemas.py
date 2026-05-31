# retrieval/schemas.py

TOPIC_FORMAT_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "spans": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
                "required": ["name", "description", "spans"],
            },
            "minItems": 3,
            "maxItems": 10,
        }
    },
    "required": ["topics"],
}
