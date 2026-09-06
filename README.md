# Long-Horizon AI Consistency — URAP take-home

A small symbolic story, a rule-based consistency checker for it, and a harness for
comparing that checker against an AI judge on the same traces.

No LLM is involved in any checking decision. `checker.py` is ordinary Python.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install pytest

.venv/bin/python run_checker.py        # verdict for every trace in traces.json
.venv/bin/python -m pytest -q          # 20 tests
```

## Files

| file | what it is |
|---|---|
| `story.py` | the world: initial state, the seven event schemas (precondition + effect) |
| `checker.py` | the checker: preconditions, invariants, panel comparison, first-violation reporting |
| `traces.json` | the world description and 9 traces (4 valid, 5 invalid) with expected verdicts |
| `run_checker.py` | runs every trace and prints the report |
| `test_checker.py` | the trace table as an acceptance suite, plus unit tests for rules and edge cases |
| `make_ai_prompt.py` | builds the blind prompt for the AI judge and a private answer key |
| `ai_eval/prompt.md` | what gets pasted into the AI. Contains no verdicts |
| `ai_eval/key.json` | letter → trace mapping and the checker's answers. Not shown to the AI |
| `ai_eval/score.py` | scores a transcribed AI answer sheet against the checker |
| `REPORT.md` | the write-up |

## The story

Two characters (Jake, Marcus), two objects (a lantern, a brass key), one container
(a chest), three locations (hall, study, garden). Jake starts in the hall with the
lantern on the floor; Marcus starts in the study with the key locked in the chest.

## The rules

| id | rule |
|---|---|
| `E-PRE` | an event may only occur if its preconditions hold |
| `I1` | custody coherence: an object's location equals that of whoever or whatever holds it |
| `I2` | object permanence: nothing appears or vanishes |
| `I3` | no unexplained restoration: broken → intact only via a `repair` event |
| `I4` | concealment: an object in a closed container cannot be acted on or leave it |
| `P1` | panel agreement: an observed panel must match the state the events predict |

## Comparing against an AI judge

```bash
.venv/bin/python make_ai_prompt.py            # regenerates prompt.md + key.json
# paste ai_eval/prompt.md into the AI, transcribe its table into an answers file
cp ai_eval/answers_TEMPLATE.txt ai_eval/answers_chatgpt.txt
.venv/bin/python ai_eval/score.py ai_eval/answers_chatgpt.txt
```

The prompt shuffles the traces with a fixed seed and relabels them A–I, so the
valid-then-invalid ordering of `traces.json` does not leak the answers.
