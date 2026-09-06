"""Domain model for a small symbolic visual story.

A *state* is a snapshot of the world (one comic panel). An *event* is the action
that happens between two panels. A *trace* is an initial state plus a sequence of
steps, where each step is an event and (optionally) the panel that was observed
after it.

Objects live in exactly one of three places:
  - held by a character   (holder set, container None)
  - inside a container    (holder None, container set)
  - lying in a location   (holder None, container None)
`location` is always populated and must agree with whoever/whatever holds it.
"""

from copy import deepcopy

# ---------------------------------------------------------------- initial world

INITIAL_STATE = {
    "characters": {
        "jake": {"location": "hall"},
        "marcus": {"location": "study"},
    },
    "objects": {
        "lantern": {"location": "hall", "holder": None, "container": None,
                    "condition": "intact"},
        "key": {"location": "study", "holder": None, "container": "chest",
                "condition": "intact"},
    },
    "containers": {
        "chest": {"location": "study", "open": False},
    },
}

LOCATIONS = ["hall", "study", "garden"]


def object_place(state, obj):
    """Where an object can be reached from: its holder, its container, or a room."""
    o = state["objects"][obj]
    if o["holder"]:
        return ("held", o["holder"])
    if o["container"]:
        return ("in", o["container"])
    return ("at", o["location"])


def reachable(state, actor, obj):
    """An actor can act on an object it holds, or that is loose/open in its room."""
    o = state["objects"][obj]
    here = state["characters"][actor]["location"]
    if o["holder"] == actor:
        return True
    if o["location"] != here:
        return False
    if o["container"]:
        return state["containers"][o["container"]]["open"]
    return o["holder"] is None


# ------------------------------------------------------------- event schemas
# Each schema is (precondition, effect). The precondition returns an error string
# when the event cannot happen in `state`, else None.

def _pre_move(s, e):
    if e["to"] not in LOCATIONS:
        return f"{e['to']} is not a location"
    if s["characters"][e["actor"]]["location"] == e["to"]:
        return f"{e['actor']} is already in the {e['to']}"
    return None


def _eff_move(s, e):
    actor, to = e["actor"], e["to"]
    s["characters"][actor]["location"] = to
    for o in s["objects"].values():          # carried objects travel along
        if o["holder"] == actor:
            o["location"] = to


def _pre_take(s, e):
    actor, obj = e["actor"], e["obj"]
    o = s["objects"][obj]
    if o["holder"] == actor:
        return f"{actor} is already holding the {obj}"
    if o["holder"] is not None:
        return f"the {obj} is held by {o['holder']}, not free to take"
    if o["location"] != s["characters"][actor]["location"]:
        return (f"the {obj} is in the {o['location']} but {actor} is in the "
                f"{s['characters'][actor]['location']}")
    if o["container"] and not s["containers"][o["container"]]["open"]:
        return f"the {obj} is inside the closed {o['container']}"
    return None


def _eff_take(s, e):
    o = s["objects"][e["obj"]]
    o["holder"], o["container"] = e["actor"], None


def _pre_give(s, e):
    actor, obj, to = e["actor"], e["obj"], e["to"]
    o = s["objects"][obj]
    if o["holder"] != actor:
        holder = o["holder"] or "nobody"
        return f"{actor} cannot give the {obj}: it is held by {holder}"
    if s["characters"][actor]["location"] != s["characters"][to]["location"]:
        return (f"{actor} is in the {s['characters'][actor]['location']} but {to} "
                f"is in the {s['characters'][to]['location']}")
    return None


def _eff_give(s, e):
    s["objects"][e["obj"]]["holder"] = e["to"]


def _pre_drop(s, e):
    if s["objects"][e["obj"]]["holder"] != e["actor"]:
        return f"{e['actor']} is not holding the {e['obj']}"
    return None


def _eff_drop(s, e):
    o = s["objects"][e["obj"]]
    o["holder"] = None
    o["location"] = s["characters"][e["actor"]]["location"]


def _pre_open(s, e):
    c = s["containers"][e["container"]]
    if c["location"] != s["characters"][e["actor"]]["location"]:
        return f"{e['actor']} is not in the {c['location']} with the {e['container']}"
    if c["open"]:
        return f"the {e['container']} is already open"
    return None


def _eff_open(s, e):
    s["containers"][e["container"]]["open"] = True


def _pre_break(s, e):
    o = s["objects"][e["obj"]]
    if not reachable(s, e["actor"], e["obj"]):
        return f"{e['actor']} cannot reach the {e['obj']}"
    if o["condition"] == "broken":
        return f"the {e['obj']} is already broken"
    return None


def _eff_break(s, e):
    s["objects"][e["obj"]]["condition"] = "broken"


def _pre_repair(s, e):
    o = s["objects"][e["obj"]]
    if not reachable(s, e["actor"], e["obj"]):
        return f"{e['actor']} cannot reach the {e['obj']}"
    if o["condition"] != "broken":
        return f"the {e['obj']} is not broken"
    return None


def _eff_repair(s, e):
    s["objects"][e["obj"]]["condition"] = "intact"


EVENTS = {
    "move":   (_pre_move,   _eff_move),
    "take":   (_pre_take,   _eff_take),
    "give":   (_pre_give,   _eff_give),
    "drop":   (_pre_drop,   _eff_drop),
    "open":   (_pre_open,   _eff_open),
    "break":  (_pre_break,  _eff_break),
    "repair": (_pre_repair, _eff_repair),
}


def apply_event(state, event):
    """Return the state predicted by applying `event`. Caller checks preconditions."""
    nxt = deepcopy(state)
    EVENTS[event["action"]][1](nxt, event)
    return nxt


def describe(event):
    a = event["action"]
    if a == "move":
        return f"{event['actor']} moves to the {event['to']}"
    if a == "give":
        return f"{event['actor']} gives the {event['obj']} to {event['to']}"
    if a == "open":
        return f"{event['actor']} opens the {event['container']}"
    return f"{event['actor']} {a}s the {event['obj']}"
