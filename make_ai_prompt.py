"""Generate the blind prompt for the AI judge, plus a private answer key.

Traces are shuffled with a fixed seed and relabelled A..I so that the ordering of
traces.json (valid first) does not leak the answers. The AI is given the same
world model and the same rules the checker enforces, but never a verdict.
"""

import json
import random

from checker import check_trace
from story import INITIAL_STATE, describe

SEED = 20250905

PREAMBLE = """\
You are checking short symbolic stories for continuity errors, the way one would
check a comic for a panel that contradicts what came before.

# World

Locations: hall, study, garden.
Characters: Jake, Marcus.
Objects: a lantern, a brass key.
Containers: a chest.

Initial state (before step 1 of every story):
- Jake is in the hall. Marcus is in the study.
- The lantern is lying on the floor of the hall, intact, held by nobody.
- The chest is in the study and is closed.
- The brass key is inside the closed chest, intact.

# What events mean

- move(actor, to): the actor walks to another location. Anything the actor is
  holding travels with them.
- take(actor, obj): the actor picks up an object. Only possible if the object is
  in the actor's location, held by nobody, and not inside a closed container.
- give(actor, obj, recipient): only possible if the actor is currently holding
  the object and both characters are in the same location.
- drop(actor, obj): the actor must be holding the object; it is left on the floor
  of the actor's current location.
- open(actor, container): the actor must be in the container's location and the
  container must be closed.
- break(actor, obj): the actor must be able to reach the object, which must be
  intact. It becomes broken.
- repair(actor, obj): the actor must be able to reach the object, which must be
  broken. It becomes intact.

# Rules

E-PRE  An event may only happen if its preconditions above hold.
I1     An object's location must equal the location of whoever or whatever holds
       it. An object cannot be in two places, or be held and inside a chest.
I2     No object may appear or vanish. The world always contains exactly the
       lantern and the key.
I3     An object's condition may only go from broken back to intact through an
       explicit repair event.
I4     An object inside a closed container cannot be acted on or leave it.
P1     Where a story states what a panel shows, the panel must agree with the
       state the events imply.

# Your task

For each story below, decide whether it is VALID (no rule is broken) or INVALID.
If it is INVALID, give the number of the FIRST step at which a rule is broken,
and which rule (E-PRE, I1, I2, I3, I4, or P1).

Answer as a table with one row per story: story letter, VALID/INVALID, first
violating step (or "-"), rule (or "-"), and one sentence of justification.
Do not write code. Reason directly about the stories.
"""


def render_observed(observed):
    bits = []
    for name, f in observed.get("characters", {}).items():
        bits.append(f"{name} is in the {f['location']}"
                    if "location" in f else f"{name}: {f}")
    for name, f in observed.get("objects", {}).items():
        for k, v in f.items():
            if k == "holder":
                bits.append(f"the {name} is held by {v}" if v
                            else f"the {name} is held by nobody")
            elif k == "container":
                bits.append(f"the {name} is inside the {v}" if v
                            else f"the {name} is not inside anything")
            elif k == "location":
                bits.append(f"the {name} is in the {v}")
            else:
                bits.append(f"the {name} is {v}")
    for name in observed.get("absent", []):
        bits.append(f"the {name} is nowhere to be seen")
    return "; ".join(bits)


def render(letter, trace):
    lines = [f"## Story {letter}", ""]
    for i, step in enumerate(trace["steps"], start=1):
        line = f"{i}. {describe(step['event'])}."
        if "observed" in step:
            line += f" The panel then shows: {render_observed(step['observed'])}."
        lines.append(line)
    return "\n".join(lines)


def main():
    data = json.load(open("traces.json"))
    traces = list(data["traces"])
    random.Random(SEED).shuffle(traces)

    key, blocks = [], []
    for n, t in enumerate(traces):
        letter = chr(ord("A") + n)
        blocks.append(render(letter, t))
        result = check_trace(INITIAL_STATE, t["steps"])
        v = result["violation"]
        key.append({
            "letter": letter,
            "trace_id": t["id"],
            "label": t["label"],
            "checker": {"valid": result["valid"],
                        "step": v["step"] if v else None,
                        "rule": v["rule"] if v else None},
        })

    with open("ai_eval/prompt.md", "w") as f:
        f.write(PREAMBLE + "\n" + "\n\n".join(blocks) + "\n")
    with open("ai_eval/key.json", "w") as f:
        json.dump(key, f, indent=2)
    print(f"wrote ai_eval/prompt.md ({len(traces)} stories) and ai_eval/key.json")


if __name__ == "__main__":
    main()
