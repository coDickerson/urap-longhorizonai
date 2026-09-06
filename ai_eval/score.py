"""Score an AI judge's answers against the checker.

Usage: python ai_eval/score.py ai_eval/answers_<model>.txt

The answers file has one line per story, whitespace separated:

    A INVALID 3 E-PRE
    B VALID - -

Lines starting with # are ignored. Step and rule may be "-" for VALID stories,
or "?" if the AI declined to commit to one.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def parse(path):
    answers = {}
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        letter, verdict = parts[0].upper(), parts[1].upper()
        step = parts[2] if len(parts) > 2 else "-"
        rule = parts[3] if len(parts) > 3 else "-"
        answers[letter] = {
            "valid": verdict.startswith("V"),
            "step": int(step) if step.isdigit() else None,
            "rule": None if rule in ("-", "?") else rule.upper(),
        }
    return answers


def main(path):
    key = json.load(open(os.path.join(HERE, "key.json")))
    traces = {t["id"]: t for t in
              json.load(open(os.path.join(ROOT, "traces.json")))["traces"]}
    answers = parse(path)

    rows, buckets = [], {}
    for k in key:
        a = answers.get(k["letter"])
        c = k["checker"]
        exp = traces[k["trace_id"]]["expected"]
        dist = exp.get("distance")
        if a is None:
            rows.append((k, None, "MISSING", dist))
            continue
        if a["valid"] != c["valid"]:
            grade = "DISAGREE (verdict)"
        elif c["valid"]:
            grade = "AGREE"
        elif a["step"] != c["step"]:
            grade = f"PARTIAL (step {a['step']} vs {c['step']})"
        elif a["rule"] != c["rule"]:
            grade = f"PARTIAL (rule {a['rule']} vs {c['rule']})"
        else:
            grade = "AGREE"
        rows.append((k, a, grade, dist))
        if dist is not None:
            b = "long (>=4 steps)" if dist >= 4 else "short (<4 steps)"
            buckets.setdefault(b, []).append(grade == "AGREE")

    w = 8
    print(f"{'story':<6}{'trace':<{w}}{'checker':<22}{'ai':<22}{'result'}")
    for k, a, grade, dist in rows:
        c = k["checker"]
        cs = "valid" if c["valid"] else f"invalid s{c['step']} {c['rule']}"
        if a is None:
            as_ = "-"
        else:
            as_ = "valid" if a["valid"] else f"invalid s{a['step']} {a['rule']}"
        print(f"{k['letter']:<6}{k['trace_id']:<{w}}{cs:<22}{as_:<22}{grade}")

    n = len(rows)
    full = sum(1 for *_, g, _ in rows if g == "AGREE")
    verdict_only = sum(1 for _, a, g, _ in rows
                       if a is not None and not g.startswith("DISAGREE"))
    print(f"\nexact agreement (verdict + step + rule): {full}/{n}")
    print(f"verdict agreement (valid vs invalid):    {verdict_only}/{n}")
    for b in sorted(buckets):
        hits = buckets[b]
        print(f"  {b}: {sum(hits)}/{len(hits)} exact")


if __name__ == "__main__":
    main(sys.argv[1])
