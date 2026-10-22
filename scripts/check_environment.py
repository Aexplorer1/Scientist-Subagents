#!/usr/bin/env python3
"""Read-only checks for installing Scientist Subagents in local Codex."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


def run_cli(executable: str, *args: str) -> str:
    result = subprocess.run(
        [executable, *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=30,
    )
    if result.returncode:
        # Do not echo arbitrary configuration diagnostics, which can contain secrets.
        raise RuntimeError(f"codex {' '.join(args)} failed (exit {result.returncode})")
    return result.stdout.strip()


def inspect_features(output: str) -> dict[str, bool]:
    features = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[-1] in ("true", "false"):
            features[parts[0]] = parts[-1] == "true"
    return features


def main() -> int:
    if sys.version_info < (3, 11):
        print("MISSING: Python 3.11+ is required for this environment checker (TOML support).")
        print("The name helper itself supports Python 3.10+.")
        return 1
    import tomllib

    root = Path(__file__).resolve().parent.parent
    missing = False
    for relative in ("SKILL.md", "agents/openai.yaml", "scripts/pick_names.py", "README.md"):
        exists = (root / relative).is_file()
        print(f"{'OK' if exists else 'MISSING'}: {relative}")
        missing |= not exists

    from pick_names import NAMES, pick_names
    names = pick_names(len(NAMES))
    if len(set(names)) != len(NAMES) or not all(n.isascii() and n.islower() and n.isalpha() for n in names):
        raise RuntimeError("name helper returned an invalid pool")
    print(f"OK: Python {sys.version.split()[0]}, name helper ({len(names)} unique names)")

    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_path = codex_home / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
    agents = config.get("agents", {})
    if agents.get("enabled", True) is False:
        print("MISSING: [agents] enabled = false; enable it in config.toml")
        missing = True
    if agents.get("max_concurrent_threads_per_session", agents.get("max_threads", 3)) < 2:
        print("MISSING: agent concurrency is below two; independent parallel work needs two slots")
        missing = True
    installed_skill = (root / "SKILL.md").resolve()
    for item in config.get("skills", {}).get("config", []):
        candidate = Path(item.get("path", "")).expanduser()
        if candidate.resolve() in (root, installed_skill) and item.get("enabled", True) is False:
            print("MISSING: this skill is disabled in [[skills.config]]")
            missing = True

    executable = shutil.which("codex.cmd") if os.name == "nt" else None
    executable = executable or shutil.which("codex")
    if not executable:
        print("MISSING: codex CLI is not on PATH; verify the desktop client settings manually")
        return 1
    version = run_cli(executable, "--version")
    print(f"OK: {version}")
    features = inspect_features(run_cli(executable, "features", "list"))
    for name in ("multi_agent", "multi_agent_v2"):
        if features.get(name):
            print(f"OK: {name} enabled")
        elif name in features:
            print(f"MISSING: run `codex features enable {name}` and start a new session")
            missing = True
        else:
            print(f"MISSING: CLI does not list {name}; check version compatibility in README.md")
            missing = True
    print("NEXT: In a new Codex session, verify spawn_agent accepts task_name, then follow README's smoke test.")
    print("These checks do not inspect live model tools or prove desktop sidebar behavior.")
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: environment check could not complete ({type(error).__name__}); inspect local installation/configuration.", file=sys.stderr)
        raise SystemExit(2)
