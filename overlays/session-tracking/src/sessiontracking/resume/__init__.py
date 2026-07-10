"""The resume product: a configurable session-start summary.

`resume.sh` used to be six hardcoded bash sections — what it printed, in what order,
filtered how, was source code. A repo that wanted a different summary had to edit the
script, which is why `resume.sh` needed an overlay keep-region at all.

Now the steps are data (`resume.yaml`) and this package interprets them. `region:` steps
name a **register role**, resolved through `sessiontracking.register` — the same resolver
the handoff writes with, so read and write can never disagree about a region's boundaries.

See docs/plans/resume-config-steps.md (R-D1, R-D2, R-D3).
"""

from .config import ResumeConfig, ResumeConfigError, Step, load_resume_config

__all__ = ["ResumeConfig", "ResumeConfigError", "Step", "load_resume_config"]
