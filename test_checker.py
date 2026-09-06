"""Tests for the consistency checker.

The trace table in traces.json is the acceptance suite; the rest are unit tests
for rules that no trace happens to exercise, plus edge cases found while writing
the checker.
"""

import json
from copy import deepcopy

import pytest

from checker import check_trace
from story import INITIAL_STATE, apply_event

TRACES = json.load(open("traces.json"))["traces"]


@pytest.mark.parametrize("t", TRACES, ids=[t["id"] for t in TRACES])
def test_trace_verdicts(t):
    result = check_trace(INITIAL_STATE, t["steps"])
    exp = t["expected"]
    assert result["valid"] == exp["valid"], result["violation"]
    if not exp["valid"]:
        assert result["violation"]["step"] == exp["step"]
        assert result["violation"]["rule"] == exp["rule"]


def test_checker_does_not_mutate_the_initial_state():
    before = deepcopy(INITIAL_STATE)
    check_trace(INITIAL_STATE, TRACES[0]["steps"])
    assert INITIAL_STATE == before


def test_first_violation_is_reported_not_a_later_one():
    steps = [
        {"event": {"action": "take", "actor": "marcus", "obj": "lantern"}},   # bad
        {"event": {"action": "take", "actor": "jake", "obj": "key"}},        # also bad
    ]
    v = check_trace(INITIAL_STATE, steps)["violation"]
    assert v["step"] == 1


def test_i1_custody_coherence_teleported_object():
    # The panel leaves the lantern behind in the hall while Jake carries it away.
    steps = [
        {"event": {"action": "take", "actor": "jake", "obj": "lantern"}},
        {"event": {"action": "move", "actor": "jake", "to": "garden"},
         "observed": {"objects": {"lantern": {"location": "hall"}}}},
    ]
    v = check_trace(INITIAL_STATE, steps)["violation"]
    assert (v["step"], v["rule"]) == (2, "I1")


def test_concealment_blocks_taking_from_a_closed_container():
    # Enforced at the precondition layer, so it is reported as E-PRE, not I4.
    steps = [
        {"event": {"action": "take", "actor": "marcus", "obj": "key"}},
    ]
    v = check_trace(INITIAL_STATE, steps)["violation"]
    assert v["rule"] == "E-PRE"
    assert "closed chest" in v["detail"]


def test_i4_panel_may_not_show_an_object_out_of_a_closed_container():
    # No take event, so only the panel puts the key outside the chest.
    steps = [
        {"event": {"action": "move", "actor": "marcus", "to": "hall"},
         "observed": {"objects": {"key": {"container": None}}}},
    ]
    v = check_trace(INITIAL_STATE, steps)["violation"]
    assert (v["step"], v["rule"]) == (1, "I4")


def test_i2_object_may_not_appear_from_nowhere():
    steps = [
        {"event": {"action": "take", "actor": "jake", "obj": "lantern"},
         "observed": {"objects": {"ghost": {"location": "hall", "holder": None,
                                            "container": None,
                                            "condition": "intact"}}}},
    ]
    v = check_trace(INITIAL_STATE, steps)["violation"]
    assert (v["step"], v["rule"]) == (1, "I2")


def test_repair_licenses_restoration_only_for_the_repaired_object():
    # Repairing the lantern must not excuse the key becoming intact again.
    state = deepcopy(INITIAL_STATE)
    state["objects"]["lantern"]["holder"] = "jake"
    state["objects"]["lantern"]["condition"] = "broken"
    state["objects"]["key"]["condition"] = "broken"
    steps = [
        {"event": {"action": "repair", "actor": "jake", "obj": "lantern"},
         "observed": {"objects": {"key": {"condition": "intact"}}}},
    ]
    v = check_trace(state, steps)["violation"]
    assert v["rule"] == "I3"
    assert "key" in v["detail"]


def test_carried_objects_move_with_their_holder():
    state = deepcopy(INITIAL_STATE)
    state["objects"]["lantern"]["holder"] = "jake"
    nxt = apply_event(state, {"action": "move", "actor": "jake", "to": "garden"})
    assert nxt["objects"]["lantern"]["location"] == "garden"


def test_dropped_object_stays_behind_when_its_holder_leaves():
    steps = [
        {"event": {"action": "take", "actor": "jake", "obj": "lantern"}},
        {"event": {"action": "drop", "actor": "jake", "obj": "lantern"}},
        {"event": {"action": "move", "actor": "jake", "to": "garden"},
         "observed": {"objects": {"lantern": {"location": "hall"}}}},
    ]
    assert check_trace(INITIAL_STATE, steps)["valid"]


def test_empty_trace_is_valid():
    assert check_trace(INITIAL_STATE, [])["valid"]


def test_unknown_action_is_reported_not_raised():
    v = check_trace(INITIAL_STATE,
                    [{"event": {"action": "teleport", "actor": "jake"}}])["violation"]
    assert v["rule"] == "E-PRE"
