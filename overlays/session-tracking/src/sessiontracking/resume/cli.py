"""`st-resume` — render the session-start summary from resume.yaml."""

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

from sessiontracking.register import RegistryError, load_register

from .config import ResumeConfigError, load_resume_config
from .steps import Context, StepError, render


def _default_repo_root() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return str(Path.cwd())


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="st-resume", description="Session-start summary")
    parser.add_argument("--repo-root")
    parser.add_argument("--registry", help="default: <repo-root>/.claude/handoff/registry.yaml")
    parser.add_argument("--config", help="default: <repo-root>/.claude/resume.yaml")
    parser.add_argument("--date", help="override the {date} substitution (testing)")
    return parser.parse_args(argv)


def _resolve_paths(args) -> tuple[Path, Path]:
    repo_root = Path(args.repo_root or _default_repo_root())
    return repo_root, Path(args.config or repo_root / ".claude" / "resume.yaml")


def _resolve_registry(args, repo_root: Path, config) -> Path:
    """Precedence: --registry > resume.yaml's `registry:` > the default location."""
    if args.registry:
        return Path(args.registry)
    if config.registry:
        return repo_root / config.registry
    return repo_root / ".claude" / "handoff" / "registry.yaml"


def _build_context(args, repo_root: Path, registry_path: Path) -> Context:
    date = args.date or datetime.date.today().isoformat()
    return Context(repo_root, load_register(registry_path), date)


def _render_all(config, ctx: Context) -> str:
    lines = []
    for step in config.steps:
        lines.extend(render(step, ctx))
    return "\n".join(lines)


def main(argv=None) -> int:
    args = _parse_args(argv)
    repo_root, config_path = _resolve_paths(args)
    try:
        config = load_resume_config(config_path)
        registry_path = _resolve_registry(args, repo_root, config)
        ctx = _build_context(args, repo_root, registry_path)
        print(_render_all(config, ctx))
    except (RegistryError, ResumeConfigError, StepError) as e:
        print(f"st-resume: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
