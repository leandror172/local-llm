"""The register primitive: where a tracked region lives, and how to resolve it.

This is a **layer-0 primitive**, not a product. Both `sessiontracking.handoff` (which
writes regions) and `sessiontracking.resume` (which reads them) depend on it; neither
depends on the other. Dependencies point down only — see `ref:model-registry-library-decision`
("products depend on primitives, never product↔product").

Sharing the resolver is the point: read and write can never disagree about where a
region begins, because there is exactly one `locate()`.

Layering rule: PyYAML is confined to `registry_io`. `locator` stays stdlib-only, as it is
the handoff's safety core.
"""

from .locator import Region, LocatorError, locate
from .registry_io import (
    RegistryError,
    SUPPORTED_REGISTER_SCHEMA,
    load_register,
)

__all__ = [
    "Region",
    "LocatorError",
    "locate",
    "RegistryError",
    "SUPPORTED_REGISTER_SCHEMA",
    "load_register",
]
