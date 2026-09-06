"""Run the checker over every trace in traces.json and print a report."""

import json
import sys

from checker import check_trace
from story import INITIAL_STATE


def main(path="traces.json"):
    data = json.load(open(path))
    failures = 0
    for t in data["traces"]:
        result = check_trace(INITIAL_STATE, t["steps"])
        v = result["violation"]
        verdict = "VALID" if result["valid"] else (
            f"INVALID at step {v['step']} [{v['rule']}]")
        print(f"{t['id']}  {verdict}")
        print(f"    {t['label']}")
        if v:
            print(f"    step {v['step']}: {v['event']}")
            print(f"    {v['rule']}: {v['detail']}")
        exp = t["expected"]
        ok = (result["valid"] == exp["valid"]
              and (result["valid"] or (v["step"] == exp["step"]
                                       and v["rule"] == exp["rule"])))
        if not ok:
            failures += 1
            print(f"    !! expected {exp}")
        print()
    print(f"{len(data['traces'])} traces, {failures} mismatches")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
