"""Session-tracking: deterministic session continuity tooling for Claude Code repos.

Two products over one primitive:

    register/   where a tracked region lives + how to resolve it   (primitive)
      ^     ^
    handoff/  resume/                                              (products)

`handoff` writes regions at session end; `resume` reads them at session start. They share
`register` and know nothing of each other.

Distribution (R-D9, docs/plans/resume-config-steps.md): **code ships as a package, config
ships as an overlay.** This package carries no per-repo state; `registry.yaml`, `resume.yaml`,
the starter templates, and the CLAUDE.md section are installed per-repo by `install-overlay.py`.
"""

__version__ = "11.0.0"
