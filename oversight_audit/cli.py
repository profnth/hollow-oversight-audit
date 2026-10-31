"""Command-line interface.

  python -m oversight_audit simulate --n 2000 --seed 1
  python -m oversight_audit generate --n 200 --out items.jsonl --reviewer-view queue.jsonl
  python -m oversight_audit audit --key items.jsonl --decisions decisions.csv
"""

from __future__ import annotations

import argparse
import json

from . import audit, scenarios, simulate


def _fmt(x):
    if x is None:
        return "  n/a"
    return f"{x:5.2f}"


def cmd_simulate(a):
    items = scenarios.generate(a.n, seed=a.seed, harmful_rate=a.harmful_rate,
                               adversarial_rate=a.adversarial_rate)
    human = simulate.HumanReviewer(time_pressure=a.time_pressure)
    checker = simulate.AIChecker()
    print(f"{a.n} simulated items, seed {a.seed}, time pressure {a.time_pressure}")
    print("Simulated reviewers: for piloting only, not evidence about people.\n")
    header = f"{'structure':24} {'catch':>6} {'catch-adv':>9} {'catch-irrev':>11} {'false-rej':>9} {'hollow':>7} {'human-min':>10}"
    print(header)
    print("-" * len(header))
    for name in simulate.STRUCTURES:
        rows = simulate.run_structure(name, items, human, checker, seed=a.seed)
        dec = {r["id"]: r["approve"] for r in rows}
        mins = {r["id"]: r["minutes"] for r in rows}
        r = audit.score(items, dec, mins)
        print(f"{name:24} {_fmt(r['catch_rate']):>6} {_fmt(r['catch_rate_adversarial']):>9} "
              f"{_fmt(r['catch_rate_irreversible']):>11} {_fmt(r['false_rejection_rate']):>9} "
              f"{_fmt(r['hollowness_index']):>7} {r['human_minutes']:>10}")
    print("\ncatch = share of planted errors rejected; hollow = P(approve|error) / P(approve|correct),"
          " where 1.0 means the review does not discriminate.")


def cmd_generate(a):
    items = scenarios.generate(a.n, seed=a.seed, harmful_rate=a.harmful_rate,
                               adversarial_rate=a.adversarial_rate)
    scenarios.to_jsonl(items, a.out)
    if a.reviewer_view:
        scenarios.to_jsonl(items, a.reviewer_view, reviewer_view=True)
    print(f"Wrote {len(items)} items with answer key to {a.out}"
          + (f" and a reviewer queue without answers to {a.reviewer_view}" if a.reviewer_view else ""))


def cmd_audit(a):
    items = scenarios.from_jsonl(a.key)
    decisions, minutes = audit.read_decisions_csv(a.decisions)
    print(json.dumps(audit.score(items, decisions, minutes or None), indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(prog="oversight_audit", description="Hollow-oversight audit toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("simulate", "generate"):
        sp = sub.add_parser(name)
        sp.add_argument("--n", type=int, default=1000)
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--harmful-rate", type=float, default=0.3)
        sp.add_argument("--adversarial-rate", type=float, default=0.5)
        if name == "simulate":
            sp.add_argument("--time-pressure", type=float, default=0.3)
            sp.set_defaults(func=cmd_simulate)
        else:
            sp.add_argument("--out", required=True)
            sp.add_argument("--reviewer-view", help="also write a queue with answers removed")
            sp.set_defaults(func=cmd_generate)
    sa = sub.add_parser("audit", help="score real review decisions against an answer key")
    sa.add_argument("--key", required=True, help="JSONL answer key from `generate`")
    sa.add_argument("--decisions", required=True, help="CSV: scenario_id,decision[,minutes]")
    sa.set_defaults(func=cmd_audit)
    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
