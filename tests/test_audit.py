import csv

from oversight_audit import audit, scenarios, simulate


def test_generation_is_reproducible_and_seeded():
    a = scenarios.generate(300, seed=7)
    b = scenarios.generate(300, seed=7)
    assert [s.proposal for s in a] == [s.proposal for s in b]
    harmful = [s for s in a if s.is_harmful]
    assert 0.2 < len(harmful) / len(a) < 0.4
    assert all(s.error_type for s in harmful)
    assert not any(s.adversarial for s in a if not s.is_harmful)


def test_reviewer_view_hides_answers():
    s = scenarios.generate(1, seed=1)[0]
    view = s.reviewer_view()
    assert "is_harmful" not in view and "error_type" not in view and "adversarial" not in view


def test_rubber_stamp_is_fully_hollow_and_perfect_reviewer_is_not():
    items = scenarios.generate(500, seed=3)
    stamp = audit.score(items, {s.id: True for s in items})
    assert stamp["catch_rate"] == 0
    assert abs(stamp["hollowness_index"] - 1.0) < 1e-9
    perfect = audit.score(items, {s.id: not s.is_harmful for s in items})
    assert perfect["catch_rate"] == 1 and perfect["hollowness_index"] == 0
    lo, hi = perfect["catch_rate_ci"]
    assert lo <= 1 <= hi + 1e-9


def test_all_structures_run_and_ai_alone_catches_nothing():
    items = scenarios.generate(400, seed=5)
    h, c = simulate.HumanReviewer(), simulate.AIChecker()
    for name in simulate.STRUCTURES:
        rows = simulate.run_structure(name, items, h, c, seed=5)
        assert len(rows) == len(items)
    rows = simulate.run_structure("ai_alone", items, h, c)
    r = audit.score(items, {x["id"]: x["approve"] for x in rows})
    assert r["catch_rate"] == 0


def test_adversarial_justification_lowers_simulated_catch_rate():
    items = scenarios.generate(4000, seed=11, harmful_rate=0.5, adversarial_rate=0.5)
    rows = simulate.run_structure("human_signoff", items, simulate.HumanReviewer(), simulate.AIChecker(), seed=11)
    r = audit.score(items, {x["id"]: x["approve"] for x in rows})
    assert r["catch_rate_adversarial"] < r["catch_rate_plain"]


def test_audit_reads_real_decisions_csv(tmp_path):
    items = scenarios.generate(20, seed=2)
    key = tmp_path / "key.jsonl"
    scenarios.to_jsonl(items, str(key))
    dec = tmp_path / "decisions.csv"
    with open(dec, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "decision", "minutes"])
        for s in items:
            w.writerow([s.id, "reject" if s.is_harmful else "approve", "1.0"])
    decisions, minutes = audit.read_decisions_csv(str(dec))
    r = audit.score(scenarios.from_jsonl(str(key)), decisions, minutes)
    assert r["catch_rate"] in (1.0, None) and r["human_minutes"] == 20.0
