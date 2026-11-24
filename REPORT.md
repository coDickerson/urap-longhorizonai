# Long-Horizon AI Consistency — URAP take-home

**Cole Dickerson.** Code and README: **https://github.com/coDickerson/urap-longhorizonai**
(`run_checker.py`: 9 traces, 0 mismatches; `pytest -q`: 20 tests; judge prompt, key and scorer in `ai_eval/`.)

---

## 1. Represented story

Two characters (Jake, Marcus), two objects (a lantern, a brass key), one container
(a chest), three locations. Jake starts in the hall with the lantern on the floor;
Marcus starts in the study with the key locked inside the closed chest. A state is
a nested dictionary, a single snapshot and the analogue of one panel:

```python
{"characters": {"jake": {"location": "hall"}, ...},
 "objects": {"key": {"location": "study", "holder": None,
                     "container": "chest", "condition": "intact"}, ...},
 "containers": {"chest": {"location": "study", "open": False}}}
```

**Design choices.** *Custody is a field on the object, not a list on the
character*, so an object has one `holder` and duplication is unrepresentable in any
state the events produce. That is only half the story: a *panel* can still assert
`holder="jake"` while placing the object in a room Jake is not in. Rule I1 catches
that, and it is the claim I checked in §5.

*`location` is always populated, even for held objects, and is therefore
redundant.* That is deliberate: it is the redundancy a panel has, where you see
both the hand holding a thing and the room it is in. I1 checks the copies agree,
which is how a teleported object is caught. The price is that every effect moving a
holder must also move what they carry, guarded by a test.

*A trace is events plus optionally observed panels*, not events alone. A panel is
partial, since a panel shows only some facts, and where present it (not the
prediction) becomes the state the story continues from. This is what makes it a
model of *visual* stories rather than of a plan: in a comic the panels are the
evidence and the events are inferred, so contradictions live between the two.

**Rules.** Preconditions (`E-PRE`) say when an event may occur: you cannot take
what someone else holds, give away what you are not holding, take from a closed
chest, or repair what is not broken. Invariants are properties every panel must
satisfy:

| id | rule | needs |
|---|---|---|
| `I1` | an object's location equals that of whoever or whatever holds it | one panel |
| `I2` | object permanence: nothing appears or vanishes | two panels |
| `I3` | broken → intact only through an explicit `repair` event | two panels **+ the event** |
| `I4` | an object in a closed container cannot be acted on or leave it | two panels |
| `P1` | an observed panel must match the state the events predict | two panels + the event |

I3 is the one that matters. "The lantern is broken; six panels later it is intact"
is a continuity error or a normal plot beat depending entirely on whether a repair
happened, and no amount of looking at the two panels alone can tell you which. It
is the only rule needing the licensing event and not just the states.

**Reporting.** `check_trace` stops at the first violation and returns the step, the
event, the rule id, and a plain-English detail. Stopping is correct: after an
impossible step every later state is one the story never reached, so downstream
"violations" are artifacts. The cost is that the checker cannot count errors per
story. When a panel disagrees with the prediction, the mismatch is attributed
most-specific-first (I2 → I3 → I1 → P1); without that ordering an unexplained
repair is reported as a generic mismatch, which is true but useless.

---

## 2. Traces and results

Nine traces of six to eight events: four valid, five invalid. All produce the
expected verdict, and 20 tests pass.

| trace | verdict | first violation | cause → violation |
|---|---|---|---|
| T1 | valid | n/a | baseline custody handoff |
| T2 | valid | n/a | **legitimate** reversion, 6 steps |
| T3 | valid | n/a | key legitimately occupies four places |
| T4 | valid | n/a | observed panels, all agreeing |
| T5 | invalid | step 3, `E-PRE` | 2 steps |
| T6 | invalid | step 8, `E-PRE` | **5 steps** |
| T7 | invalid | step 7, `I3` | **5 steps** |
| T8 | invalid | step 6, `I2` | 0 steps |
| T9 | invalid | step 2, `P1` | 0 steps |

**T6 is the required long-distance error.** Jake gives the lantern to Marcus at
step 3; five steps of unrelated business follow; at step 8 Jake gives it again.
Nothing local to step 8 is wrong; it is an ordinary sentence, wrong only relative
to a fact established five steps back.

**T2 and T7 are a minimal pair, and they are the experiment.** Same story, except
T7 deletes the final `repair`. Both show the lantern broken at step 2 and whole
five or six steps later; T2 is valid, T7 is not. A judge that pattern-matches on
"state reverted" flags both; one that tracks the licence separates them. A single
invalid story measures nothing, because a model that flags every reversion scores
well on it. T3 plays the same role for location.

---

## 3. Comparison with an AI judge

**Protocol.** `make_ai_prompt.py` renders the world, the event semantics, the same
rules the checker enforces, and all nine traces into `ai_eval/prompt.md`, shuffled
with a fixed seed and relabelled A to I so the valid-then-invalid ordering cannot
leak the answer. The prompt contains no verdicts. Judge: ChatGPT 5.6 Luna, 5 Sept
2026, single pass. Scored by `ai_eval/score.py`.

```
story trace   checker            ai                 result
A     T7      invalid s7 I3      invalid s7 P1      PARTIAL (rule)
B     T9      invalid s2 P1      invalid s2 P1      AGREE
C     T4      valid              valid              AGREE
D     T1      valid              valid              AGREE
E     T2      valid              valid              AGREE
F     T8      invalid s6 I2      invalid s6 P1      PARTIAL (rule)
G     T6      invalid s8 E-PRE   invalid s8 E-PRE   AGREE
H     T5      invalid s3 E-PRE   invalid s3 E-PRE   AGREE
I     T3      valid              valid              AGREE

exact (verdict + step + rule): 7/9      verdict only: 9/9
long (>=4 steps): 2/3                   short (<4 steps): 2/3
```

**Verdict 9/9, first-violating-step 5/5, rule label 7/9.** Both misses answered
`P1`, the generic "the panel disagrees" rule, where the checker named `I3` and
`I2`. The AI used `P1` for all three panel-manifested errors and scored one exact
only because `P1` is genuinely correct for T9; on errors manifested by an
impossible *event* it was exact both times.

**The failure is taxonomy, not tracking.** Its justifications give the right
mechanism: *"the lantern was broken at step 2 and never repaired, so the panel
cannot show it as intact"* is I3, and *"dropping the key leaves it on the garden
floor, so it cannot be nowhere to be seen"* is I2. It reasoned correctly and
labelled loosely. `P1` is also not false in either case, and my rubric grades a
true-but-generic answer as a partial miss. That is defensible, since naming the
invariant is the difference between "something is off" and a diagnosis, but a
rubric scoring any true rule as correct would report 9/9. I report both. My own
checker had this same bug (§5), which suggests it is a property of the task: the
generic rule is always available and always true.

**The distance hypothesis did not survive.** I predicted localisation would degrade
with distance; it did not, at any distance tested, and the two misses split one
long and one short. Two caveats stop me concluding long-range tracking is solved.
Six to eight steps of unambiguous English is far weaker than five panels of a
comic, so the range was too short to bend the curve. More importantly, **the prompt
states the rules, I3 included**: being told broken → intact requires a repair does
much of the work on T2. This measures a judge *handed* the invariants, not one
inferring them.

**Why an AI judge might falsely flag a legitimate change.** "The world went back to
how it was" is a near-perfect surface cue for a continuity error and is also
exactly what a repair looks like. T2 and T7 present the identical observation, and
separating them means holding a specific licensing event bound to a specific
object. The further apart break and repair are, the more the judge relies on a
distant, weak detail against a strong local pattern. A detector that flags every
legitimate reversal is useless on real comics, where things routinely get fixed,
refilled, and handed back.

**Testing this on comics.** Keep the symbolic layer as ground truth and treat
images as a rendering of it: sample traces, render panels, and inject controlled
corruptions rather than hand-annotating, which gives free exact labels including
the cause-to-violation distance. Sweep that distance as the independent variable,
since the quantity of interest is a curve rather than a score, and pair every
corrupted story with its licensed twin, as T2/T7 do, or you only measure
flag-happiness. Score detection, localisation and attribution separately, since
this run showed they come apart, and ablate across text, panels, and captioned
panels to separate perception from state tracking. Only then validate on a small
hand-labelled set of real comics.

---

## 4. Reflection

**Edge cases and failure modes.** A legitimate change that looks illegitimate,
solved by feeding I3 the event and not just the state pair. Attribution of panel
mismatches, solved by most-specific-first ordering. *Partial panels*: unmentioned
facts default to what the events imply, right for comics but meaning the checker
cannot detect an error in a fact no panel shows; silence is not evidence.
*First-violation-only reporting*, which makes error counting impossible. *Redundant
`location`*, which puts the burden on every effect that moves a holder. And
`repair` licensing one object only, so repairing the lantern cannot excuse the key
becoming intact; there is a test for that.

**With another week.** First, the rules ablation: rerun the judge with the
invariants removed from the prompt, since a 9/9 verdict from a judge handed the
rules says little about one that must infer them, which is the condition a comic
presents. Second, push the distance sweep past the range where anything happened,
running distances 1 to 20 with several traces at each, and find where the curve
bends. Third, remove first-violation-only reporting so the comparison can score
recall, with attribution scored separately from detection and localisation.

**Where I could contribute, and what I would need to learn.** The evaluation
harness and the synthetic data behind it: generating traces, injecting controlled
corruptions at a chosen distance, scoring the three quantities separately. This
project is a small version of that, and what I would bring are the pieces that made
the comparison trustworthy: a blind prompt, a seeded shuffle, an answer key the
judge never sees, and a scorer that buckets by distance. Those are also the pieces
easiest to get subtly wrong, since my rubric's treatment of a true-but-generic
label moves the headline from 7/9 to 9/9. What I would need to learn is the model
side. Everything here treats the judge as a black box; I can measure that it labels
panel errors generically, but not whether that is a prompt artefact, a limit on how
state survives a long context, or something visible inside the model. Being able to
ask *where* the licensing event stops being available is the gap.

---

## 5. AI use

**Tools.** Claude (Claude Code) as a coding assistant throughout. ChatGPT appears
only as the judge under test; no LLM is involved in any decision the checker makes.

**How I worked.** I used the assistant as an implementation partner rather than an
author. I set the direction (what the experiment should test, which cases mattered,
what the comparison needed to measure) and it drafted against that while I reviewed
and redirected. On a same-day deadline it also kept the project moving and flagged
when a claim in the write-up no longer matched the data. Prompts included: design a
symbolic story meeting the character, object, event and invariant requirements;
implement a checker reporting the first violating step and the rule, with no LLM in
the loop; construct traces including one whose cause is four or more steps earlier;
build a blind prompt and scorer so the judge never sees the checker's answers; and
compare my edited report against the draft to show which justifications I had cut.

**What was AI-assisted.** The implementation and the first draft of this report
were AI-drafted against my direction and reviewed line by line. Two load-bearing
design ideas were the assistant's and adopted by me: observed panels as first-class
input, and T2/T7 as a minimal pair. Mine were running the comparison blind through
a separate model, what the scorer measures, the rewrite of §1, and reporting the
result that contradicted the design's own prediction.

**A claim I checked independently.** That *duplication is impossible by
construction*, since `holder` is a single field, implying I1 was redundant. True of
every state the simulator produces, false for the traces that matter: a panel is
merged field by field, so it can assert `holder="jake"` while placing the object in
a room Jake is not in. `test_i1_custody_coherence_teleported_object` builds exactly
that panel and confirms I1 fires. The representation prevents duplication in the
*generative* direction only; dropping I1 would leave the checker blind to the most
common visual continuity error.

**A weakness I corrected.** The first checker reported every panel disagreement
under one generic rule. It returned the right verdict on all nine traces and its
tests passed, but described T7's unexplained repair as a generic mismatch rather
than an I3 violation. Since the whole point of T2/T7 is whether a judge separates
licensed from unlicensed reversion, a checker that cannot name what it caught is a
poor baseline. The fix was most-specific-first classification, and the trace table
now asserts the rule id, not only the verdict. The instructive part is that
verdict-level tests were blind to it: the checker was right for a reason it could
not articulate. The AI judge then made the same mistake, which is why I read its
justifications rather than only its score.
