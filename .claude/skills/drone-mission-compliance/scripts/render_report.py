"""Write the mission report and the sign-off file for a person (spec §6, step 5).

The report follows the sections of the flight-plan template (S10). It proposes a decision; it
does not approve the mission. signoff.yaml has empty approval fields that only a person fills.
render_report never overwrites a sign-off file that a person started to fill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from decision import Decision, decide
from gen_plan import read_pins
from mission import MissionError, load_mission
from okf_lib import Bundle, Concept, load_bundle

APPROVER_ROLES = (  # S10 §11 Approvals
    "Remote Pilot in Command (RPIC)",
    "Mission Supervisor/Commander",
    "Safety Officer (optional)",
)
APPROVAL_FIELDS = ("name", "decision", "date")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


class SignoffError(RuntimeError):
    """A person started to fill signoff.yaml; the tool must not overwrite it."""


def _table(header: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _source_line(bundle: Bundle, concept: Concept) -> str:
    text = bundle.section(concept, "Source") or ""
    first = next((line[2:] for line in text.splitlines() if line.startswith("- ")), "")
    return _LINK.sub(r"\1", first)


def _verified(concept: Concept) -> str:
    entries = concept.frontmatter.get("verified") or []
    return ", ".join(f"{e.get('by')} {e.get('at')}" for e in entries) or "not verified"


def _command_names(bundle: Bundle) -> dict[int, str]:
    return {c.table["mavlink_id"]: c.table["name"] for c in bundle.of_type("MAVLink Command")}


def cited_concepts(validation: dict, risk: dict) -> list[str]:
    """Return every concept id that the results cite, sorted."""
    ids = {c["concept_id"] for c in validation["checks"] + risk["checks"] if c["concept_id"]}
    ids |= {r["hazard_id"] for r in risk["hazards"]}
    sora = risk["sora"]
    ids |= {v["concept_id"] for v in sora.values() if isinstance(v, dict) and v["concept_id"]}
    ids |= {m["concept_id"] for m in sora.get("mitigations_applied", [])}
    return sorted(ids)


def render(
    mission: dict,
    plan: dict,
    validation: dict,
    risk: dict,
    bundle: Bundle,
    pins: dict[str, str],
    decision: Decision,
    narrative: dict | None = None,
) -> str:
    """Return report.md. The text has no time stamp, so the same inputs give the same file.

    `narrative` is a checked summary from narrate (DRN-09); without it the report is the v1 report.
    """
    m = mission
    out: list[str] = []
    add = out.append
    add(f"# Mission report: {m['id']}")
    add("")
    add(
        f"**Proposed decision: {decision.value}** ({_count(len(decision.fails), 'failed check')}, "
        f"{_count(len(decision.gaps), 'gap')}). The tool proposes; a person decides and signs "
        "`signoff.yaml`."
    )
    add("")
    add("## 1. Mission overview")
    add("")
    mt = bundle.concepts.get(f"mission-types/{m['mission_type']}")
    add(
        _table(
            ["Mission ID", "Mission type", "Category", "Operation"],
            [[m["id"], mt.title if mt else m["mission_type"], m["category"], m["operation"]]],
        )
    )
    add("")
    add("## 2. Operational details")
    add("")
    h = m["home"]
    add(
        _table(
            ["Item", "Value"],
            [
                ["Takeoff and landing (home)", f"{h['lat']}, {h['lon']}, {h['amsl_m']} m AMSL"],
                ["Maximum altitude", f"{m['max_altitude_agl_m']} m, relative to home"],
                ["Terrain (declared)", m["terrain"]],
                ["Speed", f"{m['speed_ms']} m/s"],
                ["Area vertices", len(m["area"]["polygon"])],
                ["Geofence vertices", len(m["geofence"]["polygon"])],
                [
                    "UA",
                    (
                        f"MTOM {m['ua']['mtom_kg']} kg, {m['ua']['char_dimension_m']} m, "
                        f"{m['ua']['max_speed_ms']} m/s"
                    ),
                ],
                ["Population density (declared)", m["ground"]["population_density"]],
            ],
        )
    )
    add("")
    add("## 3. Airspace and regulatory compliance")
    add("")
    add(
        "Airspace, NOTAM, TFR and weather are **declared inputs** in v1. The tool does not check "
        f"them against a live source. Airspace class {m['airspace']['class']}, declared by "
        f"{m['airspace']['declared_by']}."
    )
    add("")
    add(
        _table(
            ["Check", "Status", "Concept", "Evidence", "Message"],
            [
                [c["check_id"], c["status"], c["concept_id"] or "none", c["evidence"], c["message"]]
                for c in validation["checks"]
            ],
        )
    )
    add("")
    add("## 4. Risk assessment")
    add("")
    add("Hazard matrix (likelihood and severity 1 to 5; score = likelihood x severity):")
    add("")
    add(
        _table(
            ["Hazard", "L", "S", "Score", "Mitigation", "Residual"],
            [
                [
                    r["hazard_id"],
                    r["likelihood"],
                    r["severity"],
                    r["score"],
                    "; ".join(r["mitigations"]),
                    r["residual"],
                ]
                for r in risk["hazards"]
            ],
        )
    )
    add("")
    sora = risk["sora"]
    if sora.get("status") == "not_applicable":
        add("SORA 2.5: not applicable (category open).")
    else:
        add("SORA 2.5 summary:")
        add("")
        rows = [
            [k, v["value"], v["concept_id"] or "none"]
            for k, v in sora.items()
            if isinstance(v, dict)
        ]
        add(_table(["Step", "Value", "Concept"], rows))
        add("")
        applied = sora.get("mitigations_applied", [])
        add(
            "Declared mitigations (operator claims; v1 does not check the Annex B criteria): "
            + (
                ", ".join(f"{a['concept_id']} {a['level']} ({a['credit']})" for a in applied)
                or "none"
            )
            + "."
        )
        add("")
        add(
            "The ARC facts use aviation units, as in the source: 500 ft AGL (152.4 m) and FL600 "
            "(a pressure altitude). See `risk/arc`, Units."
        )
        add("")
        add(
            _table(
                ["Check", "Status", "Concept", "Evidence", "Message"],
                [
                    [
                        c["check_id"],
                        c["status"],
                        c["concept_id"] or "none",
                        c["evidence"],
                        c["message"],
                    ]
                    for c in risk["checks"]
                ],
            )
        )
    add("")
    add("## 5. Flight profile and waypoint plan")
    add("")
    add("File `mission.plan` (QGroundControl plan, WGS84). Altitudes in metres relative to home.")
    add("")
    names = _command_names(bundle)
    add(
        _table(
            ["Seq", "Command", "Frame", "Latitude", "Longitude", "Altitude (m)"],
            [
                [
                    i["doJumpId"],
                    names.get(i["command"], i["command"]),
                    i["frame"],
                    i["params"][4] if "Altitude" in i else "",
                    i["params"][5] if "Altitude" in i else "",
                    i.get("Altitude", ""),
                ]
                for i in plan["mission"]["items"]
            ],
        )
    )
    add("")
    add("Failsafe settings (declared; they are vehicle parameters, not part of the plan):")
    add("")
    rows = []
    for c in bundle.of_type("Failsafe"):
        keys = c.table.get("mission_keys") or (
            {"": c.table["mission_key"]} if "mission_key" in c.table else {}
        )
        for key in keys.values():
            rows.append(
                [
                    key,
                    m["failsafes"].get(key, "not declared"),
                    c.id,
                    ", ".join(c.table["px4_params"]),
                ]
            )
    add(_table(["Failsafe", "Declared action", "Concept", "PX4 parameters"], rows))
    add("")
    add("## 6. Decision")
    add("")
    if narrative:
        add("### Summary (model-written, checked)")
        add("")
        add(narrative["summary"])
        add("")
        for item in narrative["items"]:
            add(f"- `{item['check_id']}`: {item['explanation']}")
        add("")
    add("Rule (spec §5.5): NO-GO if a check fails; else HOLD if a check is a gap; else GO.")
    add("")
    for label, items in (("Failed", decision.fails), ("Gaps", decision.gaps)):
        text = "; ".join(
            f"`{c['check_id']}` ({c['concept_id'] or 'no concept'}): {c['message']}" for c in items
        )
        add(f"- {label}: {text or 'none'}")
    add("")
    add("## 7. Audit trail")
    add("")
    concepts = [
        bundle.concepts[cid] for cid in cited_concepts(validation, risk) if cid in bundle.concepts
    ]
    add(
        _table(
            ["Concept", "Title", "Verified", "Source"],
            [[c.id, c.title, _verified(c), _source_line(bundle, c)] for c in concepts],
        )
    )
    add("")
    add(
        f"Pins: OKF `{pins['OKF_COMMIT']}`, QGC plan {pins['QGC_PLAN_VERSION']} / mission "
        f"{pins['QGC_MISSION_VERSION']}, SORA {pins['SORA_EDITION']}."
    )
    add("")
    add("## 8. Approvals")
    add("")
    add("A person fills `signoff.yaml`. The tool leaves every approval field empty.")
    return "\n".join(out) + "\n"


def signoff(mission_id: str, decision: str, plan_sha: str, report_sha: str) -> str:
    """Return signoff.yaml with empty approval fields."""
    lines = [
        "# Written by okf-drone-skill. The tool never fills the approval fields.",
        "# A person fills name, decision (GO or NO-GO) and date for each role.",
        f"mission_id: {mission_id}",
        f"proposed_decision: {decision}",
        f"plan_sha256: {plan_sha}",
        f"report_sha256: {report_sha}",
        "approvals:",
    ]
    for role in APPROVER_ROLES:
        lines.append(f'  - role: "{role}"')
        lines += [f'    {field}: ""' for field in APPROVAL_FIELDS]
    return "\n".join(lines) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _count(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def started(path: Path) -> bool:
    """Return True if signoff.yaml exists and a person filled any approval field."""
    if not path.exists():
        return False
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise SignoffError(f"{path}: not valid YAML; a person must correct it") from e
    return any(
        str(a.get(f) or "").strip() for a in doc.get("approvals") or [] for f in APPROVAL_FIELDS
    )


def inputs_sha256(out_dir: Path) -> str:
    """Return the sha256 of validation.json then risk.json: what a narrative was written for."""
    digest = hashlib.sha256()
    for name in ("validation.json", "risk.json"):
        digest.update((out_dir / name).read_bytes())
    return digest.hexdigest()


def current_narrative(out_dir: Path) -> dict | None:
    """Return narrative.json if it was written for the current results, else None."""
    path = out_dir / "narrative.json"
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc if doc.get("inputs_sha256") == inputs_sha256(out_dir) else None


def write(mission: dict, out_dir: Path, bundle: Bundle, pins: dict[str, str]) -> Decision:
    """Write report.md and signoff.yaml in out_dir. Return the proposed decision."""
    if started(out_dir / "signoff.yaml"):
        raise SignoffError(f"{out_dir / 'signoff.yaml'}: a person started the sign-off")
    plan_text = (out_dir / "mission.plan").read_text(encoding="utf-8")
    validation = json.loads((out_dir / "validation.json").read_text(encoding="utf-8"))
    risk = json.loads((out_dir / "risk.json").read_text(encoding="utf-8"))
    d = decide(validation["checks"] + risk["checks"])
    narrative = current_narrative(out_dir)
    report = render(mission, json.loads(plan_text), validation, risk, bundle, pins, d, narrative)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    text = signoff(mission["id"], d.value, _sha256(plan_text), _sha256(report))
    (out_dir / "signoff.yaml").write_text(text, encoding="utf-8")
    return d


def main(argv: list[str] | None = None) -> int:
    """Write report.md and signoff.yaml. Return 0, or 2 for a bad input or a started sign-off."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
        d = write(
            mission, args.out / mission["id"], load_bundle(args.knowledge), read_pins(args.lock)
        )
    except (MissionError, SignoffError, OSError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    print(f"wrote {args.out / mission['id'] / 'report.md'} (proposed {d.value})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
