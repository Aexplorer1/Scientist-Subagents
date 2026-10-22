#!/usr/bin/env python3
"""Select unique scientist codenames for one Codex subagent wave."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from collections.abc import Collection, Sequence


NAMES: tuple[str, ...] = (
"newton",
"einstein",
"maxwell",
"galileo",
"planck",
"bohr",
"dirac",
"heisenberg",
"schrodinger",
"faraday",
"rutherford",
"fermi",
"feynman",
"yang",
"cavendish",
"lorentz",
"curie",
"leibniz",
"euler",
"gauss",
"riemann",
"tesla",
"turing",
)


def pick_names(count: int, excluded: Collection[str] = ()) -> list[str]:
    if count <= 0:
        raise ValueError("count must be positive")

    excluded_set = set(excluded)
    available = [name for name in NAMES if name not in excluded_set]
    if count > len(available):
        raise ValueError(
            f"requested {count} names, but only {len(available)} names available"
        )

    return secrets.SystemRandom().sample(available, count)


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select unique scientist codenames for Codex subagents."
    )
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="NAME",
        help="Reserve a name so it cannot be selected; repeat as needed.",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    try:
        names = pick_names(args.count, args.exclude)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(names, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
