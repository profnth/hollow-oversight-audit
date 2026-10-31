# Hollow-Oversight Audit

A prototype toolkit from the TANDO AI Oversight Lab for testing whether human (and AI) review of AI outputs actually catches mistakes.

Many AI safety plans rely on a person approving an AI's work before it takes effect. This toolkit measures whether that approval does anything. It plants errors with known answers among correct AI outputs, sends them through a review process, and scores the decisions.

## What it does

1. **Generates seeded-error scenarios** in two task families:
   - `agent_action`: actions proposed by an AI operations agent (deleting files, sending email, running database migrations, issuing refunds, granting access). Some planted errors are irreversible.
   - `analysis`: AI summaries of a source, where the planted error is a changed number, a reversed direction, an overgeneralization, or a swapped statistic.
2. **Adds an adversarial arm.** For some planted errors, the AI's justification argues persuasively for approving it. This mirrors the AI-control threat model: a system working against its overseers.
3. **Simulates six oversight structures** for piloting and power analysis: AI alone; human alone; human sign-off; human judgment recorded before seeing the AI; an AI critic before human review; and AI-on-AI oversight with human spot checks.
4. **Audits a real review process.** Generate a queue, insert the items into any human or AI review workflow, collect approve/reject decisions in a CSV, and score them.

## The hollowness index

```
H = P(approve | planted error) / P(approve | correct item)
```

H = 1.0 means the review approves bad items as readily as good ones: oversight that is present but hollow. H = 0 means it reliably stops planted errors. The audit also reports the catch rate (overall, adversarial, and irreversible), the false-rejection rate, and human minutes spent.

## Quick start

Requires Python 3.9+. No dependencies for the offline mode.

```bash
# Simulated comparison of the six structures
python -m oversight_audit simulate --n 4000 --seed 1 --time-pressure 0.3

# Make a review queue (answers removed) plus an answer key
python -m oversight_audit generate --n 200 --out key.jsonl --reviewer-view queue.jsonl

# After reviewers decide, score them. decisions.csv columns: scenario_id,decision[,minutes]
python -m oversight_audit audit --key key.jsonl --decisions decisions.csv

# Tests
python -m pytest -q
```

## Language-model mode (optional)

`oversight_audit/llm.py` generates many more varied scenarios from the same schema and provides a language-model reviewer for the AI-critic and AI-overseer conditions.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
export OVERSIGHT_MODEL=...   # optional
```

Measured prompt sizes: a review call is about 90 input tokens; a generation call that returns five variants is about 275 input tokens.

## Important limits

- **The simulated reviewers are not evidence about people.** Their parameters (vigilance, skill, trust, susceptibility to persuasion, time pressure) are placeholder assumptions for piloting designs and sizing studies. Human experiments, under ethics review, replace them with estimates.
- All scenarios take place inside a fictional sandbox organization (`example.org`).
- In a real audit, tell reviewers in advance that some items contain deliberate errors.

## Status

Version 0.1.0, prototype. Released under the MIT License as part of the TANDO AI Oversight Lab proposal to Foresight Institute.
