"""Rule-based consistency checker. No LLM is involved in any decision here.

Two kinds of rule are enforced:

  Preconditions (E-*)  an event may only occur if the world permits it.
  Invariants    (I-*)  properties every panel must satisfy, some of which compare
                       the new panel against the previous one.

A step may carry an `observed` panel: a partial snapshot of the world, as a comic
panel would show it. When present, the observed panel — not the prediction — is
what the rest of the story is built on, and the disagreement between prediction
and observation is itself reported.
"""

from copy import deepcopy

from story import EVENTS, apply_event, describe

RULES = {
    "E-PRE": "An event's preconditions must hold in the state before it.",
    "I1": "Custody coherence: an object's location must equal the location of "
          "whoever holds it, or of the container holding it.",
    "I2": "Object permanence: the set of objects is fixed; none may appear or "
          "vanish between panels.",
    "I3": "No unexplained restoration: an object's condition may only improve "
          "from broken to intact through a repair event.",
    "I4": "Concealment: an object inside a closed container is not visible and "
          "cannot be acted on.",
    "P1": "Panel agreement: the observed panel must match the state predicted by "
          "the event.",
}


def _violation(step, event, rule, detail):
    return {
        "step": step,
        "event": describe(event) if event else None,
        "rule": rule,
        "rule_text": RULES[rule],
        "detail": detail,
    }


# --------------------------------------------------------------- invariants

def check_state_invariants(state):
    """Invariants that a single panel can be judged against. Returns (rule, detail)."""
    for name, o in state["objects"].items():
        if o["holder"]:
            holder_loc = state["characters"][o["holder"]]["location"]
            if o["location"] != holder_loc:
                return ("I1", f"the {name} is in the {o['location']} but its holder "
                              f"{o['holder']} is in the {holder_loc}")
        if o["container"]:
            box = state["containers"][o["container"]]
            if o["location"] != box["location"]:
                return ("I1", f"the {name} is in the {o['location']} but the "
                              f"{o['container']} holding it is in the {box['location']}")
            if o["holder"]:
                return ("I1", f"the {name} is inside the {o['container']} and held by "
                              f"{o['holder']} at the same time")
    return None


def check_transition_invariants(prev, nxt, event):
    """Invariants that need both panels plus the event that licensed the change."""
    if set(prev["objects"]) != set(nxt["objects"]):
        gone = set(prev["objects"]) - set(nxt["objects"])
        new = set(nxt["objects"]) - set(prev["objects"])
        what = (f"the {', '.join(sorted(gone))} vanished" if gone
                else f"the {', '.join(sorted(new))} appeared from nowhere")
        return ("I2", what)

    for name in prev["objects"]:
        before, after = prev["objects"][name], nxt["objects"][name]
        if before["condition"] == "broken" and after["condition"] == "intact":
            if not (event and event["action"] == "repair" and event["obj"] == name):
                return ("I3", f"the {name} is intact again after being broken, but no "
                              f"repair event explains it")
        # An object cannot leave a closed container without the container opening.
        if before["container"] and after["container"] is None:
            if not prev["containers"][before["container"]]["open"]:
                return ("I4", f"the {name} left the closed {before['container']}")
    return None


# ------------------------------------------------------------------ panels

def merge_panel(predicted, observed):
    """Overlay a partial observed panel onto the predicted state."""
    merged = deepcopy(predicted)
    for section in ("characters", "objects", "containers"):
        for name, fields in observed.get(section, {}).items():
            merged.setdefault(section, {}).setdefault(name, {}).update(fields)
    # An object named only in the observed panel and absent from the world, or
    # deleted by an explicit null, is handled by the object-set comparison in I2.
    for name in observed.get("absent", []):
        merged["objects"].pop(name, None)
    return merged


def _panel_disagreement(predicted, observed_state):
    for name, o in observed_state["objects"].items():
        p = predicted["objects"].get(name)
        if p is None:
            continue
        for field in ("location", "holder", "container", "condition"):
            if o[field] != p[field]:
                return (f"the panel shows the {name} with {field}={o[field]!r} but the "
                        f"event predicts {field}={p[field]!r}")
    for name, c in observed_state["characters"].items():
        p = predicted["characters"].get(name)
        if p and c["location"] != p["location"]:
            return (f"the panel shows {name} in the {c['location']} but the event "
                    f"predicts the {p['location']}")
    return None


# ------------------------------------------------------------------ checker

def check_trace(initial_state, steps):
    """Validate a trace. Returns {'valid': bool, 'violation': {...} or None}.

    Checking stops at the first violating step, as required: everything after a
    broken step is built on a world that never existed.
    """
    state = deepcopy(initial_state)

    bad = check_state_invariants(state)
    if bad:
        return {"valid": False,
                "violation": _violation(0, None, bad[0], bad[1])}

    for i, step in enumerate(steps, start=1):
        event = step["event"]
        if event["action"] not in EVENTS:
            return {"valid": False,
                    "violation": _violation(i, None, "E-PRE",
                                            f"unknown action {event['action']!r}")}

        err = EVENTS[event["action"]][0](state, event)
        if err:
            return {"valid": False, "violation": _violation(i, event, "E-PRE", err)}

        predicted = apply_event(state, event)

        if "observed" in step:
            nxt = merge_panel(predicted, step["observed"])
            # Attribute the mismatch to the most specific rule it breaks.
            bad = check_transition_invariants(state, nxt, event)
            if bad:
                return {"valid": False,
                        "violation": _violation(i, event, bad[0], bad[1])}
            bad = check_state_invariants(nxt)
            if bad:
                return {"valid": False,
                        "violation": _violation(i, event, bad[0], bad[1])}
            detail = _panel_disagreement(predicted, nxt)
            if detail:
                return {"valid": False,
                        "violation": _violation(i, event, "P1", detail)}
        else:
            nxt = predicted
            bad = (check_transition_invariants(state, nxt, event)
                   or check_state_invariants(nxt))
            if bad:
                return {"valid": False,
                        "violation": _violation(i, event, bad[0], bad[1])}

        state = nxt

    return {"valid": True, "violation": None}
