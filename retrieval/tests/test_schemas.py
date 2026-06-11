"""
Tests for retrieval/schemas.py

Covers:
- TOPIC_FORMAT_SCHEMA: is a dict
- TOPIC_FORMAT_SCHEMA: top-level type is "object"
- TOPIC_FORMAT_SCHEMA: has "topics" property
- TOPIC_FORMAT_SCHEMA: "topics" type is "array"
- TOPIC_FORMAT_SCHEMA: "topics" minItems is 3
- TOPIC_FORMAT_SCHEMA: "topics" maxItems is 10
- TOPIC_FORMAT_SCHEMA: topic item has "name" property
- TOPIC_FORMAT_SCHEMA: topic item has "description" property
- TOPIC_FORMAT_SCHEMA: topic item has "spans" property
- TOPIC_FORMAT_SCHEMA: topic item required fields are ["name", "description", "spans"]
- TOPIC_FORMAT_SCHEMA: "topics" is in schema["required"]
"""

import sys
from pathlib import Path

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

from schemas import TOPIC_FORMAT_SCHEMA  # noqa: E402


def test_topic_format_schema_is_dict():
    assert isinstance(TOPIC_FORMAT_SCHEMA, dict)


def test_topic_format_schema_top_level_type_is_object():
    assert TOPIC_FORMAT_SCHEMA["type"] == "object"


def test_topic_format_schema_has_topics_property():
    assert "topics" in TOPIC_FORMAT_SCHEMA["properties"]


def test_topics_type_is_array():
    assert TOPIC_FORMAT_SCHEMA["properties"]["topics"]["type"] == "array"


def test_topics_min_items_is_3():
    assert TOPIC_FORMAT_SCHEMA["properties"]["topics"].get("minItems") == 3


def test_topics_max_items_is_10():
    assert TOPIC_FORMAT_SCHEMA["properties"]["topics"].get("maxItems") == 10


def test_topic_item_has_name_property():
    topic_properties = TOPIC_FORMAT_SCHEMA["properties"]["topics"]["items"]["properties"]
    assert "name" in topic_properties


def test_topic_item_has_description_property():
    topic_properties = TOPIC_FORMAT_SCHEMA["properties"]["topics"]["items"]["properties"]
    assert "description" in topic_properties


def test_topic_item_has_spans_property():
    topic_properties = TOPIC_FORMAT_SCHEMA["properties"]["topics"]["items"]["properties"]
    assert "spans" in topic_properties


def test_topic_item_required_fields():
    required_fields = TOPIC_FORMAT_SCHEMA["properties"]["topics"]["items"].get("required")
    assert required_fields == ["name", "description", "spans"]


def test_schema_required_topics():
    assert "topics" in TOPIC_FORMAT_SCHEMA.get("required")
