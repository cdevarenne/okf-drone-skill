"""Score the mission risk: the hazard matrix and the SORA 2.5 summary (spec §6, step 4).

Every value comes from a verified concept. A value that cannot be found is "not_assessed" and
has a gap. score_risk writes out/<id>/risk.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle
from results import (
    FAIL,
    GAP,
    NOT_APPLICABLE,
    PASS,
    CheckResult,
    governing,
    is_verified,
    no_concept,
    result,
)

NOT_ASSESSED = "not_assessed"
ASSEMBLIES_BAND = "assemblies-of-people"  # the band name in risk/igrc for `not_over_assemblies`
M1_PREFIX = "risk/m1"  # the M1 mitigations, to which the iGRC floor applies (S2 S.4.3.4)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")

Mission = dict[str, Any]


def hazard_matrix(bundle: Bundle) -> tuple[list[dict[str, Any]], list[CheckResult]]:
    """Return one row per verified Hazard concept, and a gap if there is none."""
    rows = []
    for c in bundle.of_type("Hazard"):
        if not is_verified(c):
            continue
        fm = c.frontmatter
        mitigations = _bullets(bundle.section(c, "Mitigation") or "")
        rows.append(
            {
                "hazard_id": c.id,
                "likelihood": fm["likelihood"],
                "severity": fm["severity"],
                "score": fm["likelihood"] * fm["severity"],
                "mitigations": mitigations,
                "residual": fm["residual"],
            }
        )
    gaps = [] if rows else [no_concept("hazards.matrix")]
    return rows, gaps


def _bullets(text: str) -> list[str]:
    """Return the '- ' list items of a section, with wrapped lines joined and links as text."""
    items: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("  ") and items:
            items[-1] += " " + line.strip()
    return [_LINK.sub(r"\1", item) for item in items]


class _Sora:
    """The SORA 2.5 steps for one specific-category mission, in order."""

    def __init__(self, mission: Mission, bundle: Bundle) -> None:
        self.m, self.bundle = mission, bundle
        self.summary: dict[str, Any] = {}
        self.checks: list[CheckResult] = []

    def _add(self, key: str, value: Any, check: CheckResult) -> Any:
        self.summary[key] = {"value": value, "concept_id": check.concept_id}
        self.checks.append(check)
        return value if check.status == PASS else None

    def _skip(self, key: str, check_id: str, needs: str) -> None:
        self.summary[key] = {"value": NOT_ASSESSED, "concept_id": None}
        self.checks.append(CheckResult(check_id, GAP, None, "", f"not assessed: it needs {needs}"))

    def igrc(self) -> tuple[int, int | None] | None:
        cid = "sora.igrc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["igrc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        ua, band = self.m["ua"], self.m["ground"]["population_density"]
        row = next((r for r in c.table["rows"] if r["band"] == band), None)
        if row is None:
            bands = ", ".join(r["band"] for r in c.table["rows"])
            self._add(
                "igrc", NOT_ASSESSED, result(c, cid, GAP, f"band {band}", f"use one of: {bands}")
            )
            return None
        small = c.table["small_ua"]
        if (
            ua["mtom_kg"] <= small["max_takeoff_mass_kg"]
            and ua["max_speed_ms"] <= small["max_speed_ms"]
            and not (small["not_over_assemblies"] and band == ASSEMBLIES_BAND)
        ):
            ev = f"MTOM {ua['mtom_kg']} kg, speed {ua['max_speed_ms']} m/s"
            self._add("igrc", small["igrc"], result(c, cid, PASS, ev, "small UA rule"))
            return small["igrc"], None
        col = next(
            (
                i
                for i, k in enumerate(c.table["columns"])
                if ua["char_dimension_m"] <= k["max_dimension_m"]
                and ua["max_speed_ms"] <= k["max_speed_ms"]
            ),
            None,
        )
        ev = f"band {band}; dimension {ua['char_dimension_m']} m; speed {ua['max_speed_ms']} m/s"
        value = None if col is None else row["igrc"][col]
        if value is None:
            self._add("igrc", None, result(c, cid, FAIL, ev, "outside SORA: certified category"))
            return None
        self._add("igrc", value, result(c, cid, PASS, ev, f"iGRC {value} (column {col + 1})"))
        return value, col

    def final_grc(self, igrc: int, col: int | None) -> int | None:
        cid = "sora.final_grc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["final_grc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        declared = (self.m.get("sora") or {}).get("mitigations") or {}
        concepts = {f"risk/{k}": level for k, level in declared.items()}
        mitigations = sorted(
            (m for m in self.bundle.of_type("Mitigation") if is_verified(m)),
            key=lambda m: m.table["sequence"],
        )
        unknown = sorted(set(concepts) - {m.id for m in mitigations})
        if unknown:
            msg = f"no verified mitigation concept for {', '.join(unknown)}"
            self._add("final_grc", NOT_ASSESSED, result(c, cid, GAP, str(declared), msg))
            return None
        grc, applied = igrc, []
        floor_row = next(r for r in c.table["rows"] if r["band"] == c.table["final_grc_floor"])
        for m in mitigations:
            if m.id not in concepts:
                continue
            level = concepts[m.id]
            credit = m.table["credit"][level]
            if credit is None:
                msg = f"{m.id} has no credit at level {level}"
                self._add("final_grc", None, result(c, cid, FAIL, str(declared), msg))
                return None
            grc += credit
            applied.append({"concept_id": m.id, "level": level, "credit": credit})
            if m.id.startswith(M1_PREFIX) and col is not None:
                grc = max(grc, floor_row["igrc"][col])
        self.summary["mitigations_applied"] = applied
        ev = f"iGRC {igrc}; credits {[a['credit'] for a in applied]}"
        return self._add("final_grc", grc, result(c, cid, PASS, ev, f"final GRC {grc}"))

    def arc(self) -> str | None:
        cid = "sora.initial_arc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["initial_arc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        facts = self.m["airspace"]
        limit = c.table["above_500ft_agl_m"]
        if self.m["max_altitude_agl_m"] > limit and facts.get("above_500ft_agl") is False:
            ev = f"max_altitude_agl_m {self.m['max_altitude_agl_m']}; above_500ft_agl false"
            msg = f"the mission flies above 500 ft AGL ({limit} m) but declares it does not"
            self._add("initial_arc", NOT_ASSESSED, result(c, cid, FAIL, ev, msg))
            return None
        for rule in c.table["initial_arc"]:
            match = True
            for key, want in rule["when"].items():
                if key == "airspace_class_in":
                    match = match and facts["class"] in want
                    continue
                if key not in facts:
                    msg = f"declare airspace.{key} (true or false)"
                    self._add("initial_arc", NOT_ASSESSED, result(c, cid, GAP, "", msg))
                    return None
                match = match and facts[key] == want
            if match:
                ev = f"first matching rule: {rule['when'] or 'default'}"
                return self._add(
                    "initial_arc", rule["arc"], result(c, cid, PASS, ev, f"ARC-{rule['arc']}")
                )
        return None

    def residual_arc(self, initial: str) -> str | None:
        cid = "sora.residual_arc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["residual_arc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        order = list(c.table["tmpr"])
        res = c.table["residual_arc"]
        arc = initial
        if self.m["operation"] in res["vlos_applies_to"]:
            lowest = order.index(res["lowest_by_vlos"])
            reduced = order.index(initial) - res["vlos_reduction_classes"]
            arc = order[max(reduced, min(lowest, order.index(initial)))]
        tmpr = (
            "none (VLOS)" if self.m["operation"] in res["vlos_applies_to"] else c.table["tmpr"][arc]
        )
        self.summary["tmpr"] = {"value": tmpr, "concept_id": c.id}
        ev = f"initial ARC-{initial}; operation {self.m['operation']}"
        return self._add("residual_arc", arc, result(c, cid, PASS, ev, f"ARC-{arc}; TMPR {tmpr}"))

    def sail(self, grc: int, arc: str) -> str | None:
        cid = "sora.sail"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["sail"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        ev = f"final GRC {grc}; residual ARC-{arc}"
        row = next((r for r in c.table["rows"] if grc <= r["final_grc_max"]), None)
        if row is None:
            msg = f"final GRC above the table: {c.table['above_table']}"
            self._add("sail", None, result(c, cid, FAIL, ev, msg))
            return None
        sail = row["sail"][c.table["arc_columns"].index(arc)]
        return self._add("sail", sail, result(c, cid, PASS, ev, f"SAIL {sail}"))

    def containment(self, sail: str) -> None:
        cid = "sora.containment"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["containment"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return
        ua = self.m["ua"]
        if ua["mtom_kg"] < c.table["low_below_takeoff_mass_kg"]:
            ev = f"MTOM {ua['mtom_kg']} kg"
            self._add("containment", "low", result(c, cid, PASS, ev, "low containment"))
            return
        adjacent = (self.m.get("sora") or {}).get("adjacent_area")
        if adjacent is None:
            msg = "declare sora.adjacent_area (below_people_km2, assemblies, shelter)"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, "", msg))
            return
        table = next(
            (
                t
                for t in c.table["tables"]
                if ua["char_dimension_m"] <= t["max_dimension_m"]
                and ua["max_speed_ms"] < t["below_speed_ms"]
                and t["shelter"] == adjacent["shelter"]
            ),
            None,
        )
        if table is None:
            msg = "no containment table for this UA size, speed and shelter"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, str(adjacent), msg))
            return
        cols = table["columns"]
        kinds = list(dict.fromkeys(k["assemblies"] for k in cols))
        if adjacent["assemblies"] not in kinds:
            msg = f"assemblies must be one of: {', '.join(kinds)}"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, str(adjacent), msg))
            return
        density, kind = adjacent["below_people_km2"], kinds.index(adjacent["assemblies"])
        fits = [
            i
            for i, k in enumerate(cols)
            if kinds.index(k["assemblies"]) <= kind
            and (
                k["below_people_km2"] is None
                or (density is not None and density <= k["below_people_km2"])
            )
        ]
        row = next(r for r in table["rows"] if sail in r["sail"])
        ev = f"table {table['id']}; SAIL {sail}; adjacent area {adjacent}"
        level = row["robustness"][max(fits)] if fits else "out-of-scope"
        if level == "out-of-scope":
            self._add("containment", None, result(c, cid, FAIL, ev, "outside SORA"))
            return
        self._add("containment", level, result(c, cid, PASS, ev, f"{level} containment"))


def sora_summary(mission: Mission, bundle: Bundle) -> tuple[dict[str, Any], list[CheckResult]]:
    """Return the SORA summary and its results. Only a specific-category mission is scored."""
    c = governing(bundle, "sora.applicable")
    if c is None:
        return {"status": NOT_ASSESSED}, [no_concept("sora.applicable")]
    if mission["category"] != "specific":
        check = result(c, "sora.applicable", NOT_APPLICABLE, f"category {mission['category']}", "")
        return {"status": NOT_APPLICABLE}, [check]
    s = _Sora(mission, bundle)
    s.checks.append(result(c, "sora.applicable", PASS, "category specific", "SORA 2.5 applies"))
    got = s.igrc()
    grc = s.final_grc(*got) if got else s._skip("final_grc", "sora.final_grc", "sora.igrc")
    initial = s.arc()
    arc = (
        s.residual_arc(initial)
        if initial
        else s._skip("residual_arc", "sora.residual_arc", "sora.initial_arc")
    )
    if grc is not None and arc is not None:
        sail = s.sail(grc, arc)
    else:
        sail = s._skip("sail", "sora.sail", "the final GRC and the residual ARC")
    if sail is not None:
        s.containment(sail)
    else:
        s._skip("containment", "sora.containment", "sora.sail")
    s.checks.append(no_concept("sora.oso"))
    s.summary["oso"] = {"value": NOT_ASSESSED, "concept_id": None}
    return s.summary, s.checks


def score(mission: Mission, bundle: Bundle) -> dict[str, Any]:
    """Return the risk.json document."""
    rows, hazard_gaps = hazard_matrix(bundle)
    summary, checks = sora_summary(mission, bundle)
    return {
        "mission_id": mission["id"],
        "hazards": rows,
        "sora": summary,
        "checks": [r.to_dict() for r in hazard_gaps + checks],
    }


def main(argv: list[str] | None = None) -> int:
    """Write out/<id>/risk.json. Return 0, or 2 for a bad request."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
    except MissionError as e:
        print(e, file=sys.stderr)
        return 2
    out = args.out / mission["id"] / "risk.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(score(mission, load_bundle(args.knowledge)), indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
