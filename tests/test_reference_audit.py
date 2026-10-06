#!/usr/bin/env python3
"""Structural/provenance checks for the frozen manuscript bibliography.

This test checks the retained 69-row audit, canonical identifiers, calibration
counts, and (when run inside the full project) exact consistency with the TeX/Bib
sources.  It is deliberately not a live-Web validator and does not turn a
metadata check into a claim that every cited paper was read in full.
"""
from __future__ import annotations

import csv
import json
import re
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "reference_audit.csv"
RESULT = REPO / "results" / "reference-audit.json"
PROJECT_PAPER = REPO.parent / "paper"

EXPECTED_URLS = {
    "chaum1981": "https://doi.org/10.1145/358549.358563",
    "goldschlag1999": "https://doi.org/10.1145/293411.293443",
    "dingledine2004": "https://www.usenix.org/conference/13th-usenix-security-symposium/tor-second-generation-onion-router-0",
    "freedman2002": "https://doi.org/10.1145/586110.586137",
    "chaudhary2026": "https://doi.org/10.1145/3817115",
    "baier2008": "https://mitpress.mit.edu/9780262026499/principles-of-model-checking/",
    "corrigangibbs2010": "https://doi.org/10.1145/1866307.1866346",
    "wolinsky2012": "https://www.usenix.org/conference/osdi12/technical-sessions/presentation/wolinsky",
    "corrigangibbs2015": "https://doi.org/10.1109/SP.2015.27",
    "vandenhooff2015": "https://doi.org/10.1145/2815400.2815417",
    "angel2016": "https://www.usenix.org/conference/osdi16/technical-sessions/presentation/angel",
    "piotrowska2017": "https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/piotrowska",
    "tyagi2017": "https://doi.org/10.1145/3132747.3132783",
    "lazar2018": "https://www.usenix.org/conference/osdi18/presentation/lazar",
    "barman2018": "https://doi.org/10.2478/popets-2020-0061",
    "hintz2002": "https://doi.org/10.1007/3-540-36467-6_13",
    "sun2002": "https://doi.org/10.1109/SECPRI.2002.1004359",
    "murdoch2005": "https://doi.org/10.1109/SP.2005.12",
    "liberatore2006": "https://doi.org/10.1145/1180405.1180437",
    "hopper2007": "https://doi.org/10.1145/1315245.1315257",
    "herrmann2009": "https://doi.org/10.1145/1655008.1655013",
    "panchenko2011": "https://doi.org/10.1145/2046556.2046570",
    "mittal2011": "https://doi.org/10.1145/2046707.2046732",
    "cai2012": "https://doi.org/10.1145/2382196.2382260",
    "wang2013": "https://doi.org/10.1145/2517840.2517851",
    "johnson2013": "https://doi.org/10.1145/2508859.2516651",
    "wang2014": "https://www.usenix.org/conference/usenixsecurity14/technical-sessions/presentation/wang_tao",
    "juarez2014": "https://doi.org/10.1145/2660267.2660368",
    "hayes2016": "https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/hayes",
    "rimmer2018": "https://doi.org/10.14722/ndss.2018.23105",
    "sirinam2018": "https://doi.org/10.1145/3243734.3243768",
    "nasr2018": "https://doi.org/10.1145/3243734.3243824",
    "rahman2020": "https://doi.org/10.2478/popets-2020-0043",
    "yin2022": "https://doi.org/10.1109/TDSC.2021.3104869",
    "shusterman2021": "https://doi.org/10.1109/TDSC.2020.2988369",
    "montieri2020": "https://doi.org/10.1109/TDSC.2018.2804394",
    "palmieri2021": "https://doi.org/10.1109/TDSC.2019.2947666",
    "luo2025": "https://doi.org/10.1109/TDSC.2024.3411014",
    "wright2009": "https://www.ndss-symposium.org/ndss2009/traffic-morphing-an-efficient-defense-against-statistical-traffic-analysis/",
    "shmatikov2006": "https://doi.org/10.1007/11863908_2",
    "dyer2012": "https://doi.org/10.1109/SP.2012.28",
    "cai2014": "https://doi.org/10.1145/2660267.2660362",
    "juarez2016": "https://doi.org/10.1007/978-3-319-45744-4_2",
    "wang2017": "https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/wang-tao",
    "alnaami2021": "https://doi.org/10.1109/TDSC.2019.2906390",
    "smith2022": "https://www.usenix.org/conference/usenixsecurity22/presentation/smith",
    "liu2014": "https://doi.org/10.1109/TDSC.2013.17",
    "backes2013": "https://www.ndss-symposium.org/ndss2013/ndss-2013-programme/preventing-side-channel-leaks-web-traffic-formal-approach/",
    "snader2011": "https://doi.org/10.1109/TDSC.2010.17",
    "tsang2011": "https://doi.org/10.1109/TDSC.2009.38",
    "shen2022": "https://doi.org/10.1109/TDSC.2021.3052831",
    "wu2021": "https://doi.org/10.1109/TDSC.2019.2949813",
    "wang2010stepping": "https://doi.org/10.1109/TDSC.2008.28",
    "smith2009": "https://doi.org/10.1007/978-3-642-00596-1_21",
    "alvim2012": "https://doi.org/10.1007/978-3-642-22012-8_4",
    "issa2020": "https://doi.org/10.1109/TIT.2019.2962804",
    "lindvall1992": "https://catalogue.bnf.fr/ark:/12148/cb37382125m",
    "thorisson2000": "https://doi.org/10.1007/978-1-4612-1236-2",
    "turkenburg2026": "https://doi.org/10.4230/LIPIcs.CSL.2026.25",
    "desharnais2004": "https://doi.org/10.1016/j.tcs.2003.09.013",
    "vanbreugel2005": "https://doi.org/10.1016/j.tcs.2004.09.035",
    "bacci2013": "https://doi.org/10.1007/978-3-642-40313-2_7",
    "vlasman2025": "https://doi.org/10.4230/LIPIcs.CONCUR.2025.36",
    "makur2024": "https://doi.org/10.1109/TIT.2024.3367856",
    "makur2025": "https://doi.org/10.1109/ISIT63088.2025.11195488",
    "hunter1976": "https://doi.org/10.1017/S0021900200104164",
    "fill2002": "https://doi.org/10.1007/978-94-017-0061-0_8",
    "kruskal1956": "https://doi.org/10.1090/S0002-9939-1956-0078686-7",
    "dwork2006": "https://doi.org/10.1007/11681878_14",
}

TDSC = {
    "liu2014", "alnaami2021", "yin2022", "shusterman2021",
    "montieri2020", "tsang2011", "snader2011", "palmieri2021",
    "shen2022", "wu2021", "luo2025", "wang2010stepping",
}
INFLUENTIAL = {"chaum1981", "dingledine2004", "panchenko2011", "wang2014", "sirinam2018"}
ADJACENT = {"mittal2011", "backes2013", "smith2022", "issa2020", "vlasman2025"}


def parse_bib(text: str) -> dict[str, tuple[str, dict[str, str]]]:
    """Parse the restricted brace/quote BibTeX used by the supplied manuscript."""
    entries: dict[str, tuple[str, dict[str, str]]] = {}
    offset = 0
    while True:
        match = re.search(r"@(\w+)\s*\{\s*([^,]+),", text[offset:])
        if match is None:
            break
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        cursor = offset + match.end()
        depth = 1
        quoted = False
        end = cursor
        while end < len(text) and depth:
            char = text[end]
            if char == '"' and (end == 0 or text[end - 1] != "\\"):
                quoted = not quoted
            if not quoted:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            end += 1
        if depth:
            raise AssertionError(f"unclosed BibTeX entry: {key}")
        body = text[cursor : end - 1]
        parts: list[str] = []
        start = 0
        depth = 0
        quoted = False
        for index, char in enumerate(body):
            if char == '"' and (index == 0 or body[index - 1] != "\\"):
                quoted = not quoted
            if not quoted:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                elif char == "," and depth == 0:
                    parts.append(body[start:index])
                    start = index + 1
        parts.append(body[start:])
        fields: dict[str, str] = {}
        for part in parts:
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and ((value[0] == "{" and value[-1] == "}") or (value[0] == '"' and value[-1] == '"')):
                value = value[1:-1]
            fields[name.strip().lower()] = re.sub(r"\s+", " ", value).strip()
        if key in entries:
            raise AssertionError(f"duplicate BibTeX key: {key}")
        entries[key] = (entry_type, fields)
        offset = end
    return entries


class ReferenceAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with AUDIT.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.by_key = {row["key"]: row for row in cls.rows}

    def test_inventory_and_identifiers(self) -> None:
        self.assertEqual(len(self.rows), 69)
        self.assertEqual(len(self.by_key), 69)
        self.assertEqual(set(self.by_key), set(EXPECTED_URLS))
        urls = [row["canonical_url"] for row in self.rows]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith("https://") for url in urls))
        current_additions = {"chaudhary2026", "turkenburg2026"}
        for key, url in EXPECTED_URLS.items():
            self.assertEqual(self.by_key[key]["canonical_url"], url)
            expected_date = ("2026-10-06" if key == "makur2024" else
                             "2026-09-19" if key in current_additions else "2026-09-16")
            self.assertEqual(self.by_key[key]["metadata_status"], f"manually_checked_{expected_date}")

    def test_calibration_counts_are_explicit(self) -> None:
        calibrated = {row["key"] for row in self.rows if row["full_text_calibration"] == "yes"}
        self.assertEqual(calibrated, TDSC | INFLUENTIAL | ADJACENT)
        counts = Counter(row["calibration_category"] for row in self.rows)
        self.assertEqual(counts["same-venue TDSC"], 12)
        self.assertEqual(counts["influential field paper"], 5)
        self.assertEqual(counts["adjacent venue/theory"], 5)
        self.assertEqual(counts["metadata_only"], 47)

    def test_material_corrections_are_frozen(self) -> None:
        self.assertEqual(self.by_key["chaum1981"]["authors"], "David L. Chaum")
        self.assertEqual(self.by_key["wolinsky2012"]["pages"], "179--192")
        self.assertEqual(self.by_key["barman2018"]["year"], "2020")
        self.assertEqual(self.by_key["smith2022"]["authors"].split(" and ")[0], "Jean-Pierre Smith")
        self.assertEqual(self.by_key["vanbreugel2005"]["entry_type"], "article")
        self.assertEqual(self.by_key["vanbreugel2005"]["venue"], "Theoretical Computer Science")
        self.assertEqual(self.by_key["makur2025"]["pages"], "1--6")
        self.assertEqual(self.by_key["mittal2011"]["canonical_url"], "https://doi.org/10.1145/2046707.2046732")
        self.assertEqual(self.by_key["luo2025"]["canonical_url"], "https://doi.org/10.1109/TDSC.2024.3411014")
        self.assertEqual(self.by_key["chaudhary2026"]["year"], "2026")
        self.assertEqual(self.by_key["chaudhary2026"]["pages"], "1--36")
        self.assertEqual(self.by_key["turkenburg2026"]["pages"], "25:1--25:22")
        self.assertIn("lower-bound", self.by_key["turkenburg2026"]["audit_note"])

    def test_full_project_crosscheck_when_available(self) -> None:
        bib_path = PROJECT_PAPER / "references.bib"
        tex_path = PROJECT_PAPER / "main.tex"
        if not bib_path.exists() or not tex_path.exists():
            self.skipTest("standalone repository has no paper/ sibling")
        entries = parse_bib(bib_path.read_text(encoding="utf-8"))
        self.assertEqual(set(entries), set(self.by_key))
        for key, (entry_type, fields) in entries.items():
            row = self.by_key[key]
            venue = fields.get("journal") or fields.get("booktitle") or fields.get("publisher", "")
            self.assertEqual(row["entry_type"], entry_type)
            self.assertEqual(row["authors"], fields.get("author", ""))
            self.assertEqual(row["title"], fields.get("title", ""))
            self.assertEqual(row["venue"], venue)
            self.assertEqual(row["year"], fields.get("year", ""))
            self.assertEqual(row["pages"], fields.get("pages", ""))
        cited: set[str] = set()
        for group in re.findall(r"\\cite\w*\s*\{([^}]*)\}", tex_path.read_text(encoding="utf-8")):
            cited.update(key.strip() for key in group.split(",") if key.strip())
        self.assertEqual(cited, set(entries))

    def test_doeblin_identifier_agrees_across_provenance_consumers(self) -> None:
        """Retained primary-source identity, not a live resolver or full-text audit."""
        expected = "https://doi.org/10.1109/TIT.2024.3367856"
        self.assertEqual(expected, self.by_key["makur2024"]["canonical_url"])
        with (REPO / "external_resources.csv").open(newline="", encoding="utf-8") as handle:
            resources = list(csv.DictReader(handle))
            matches = [row for row in resources
                       if row["name"] == "Doeblin Coefficients and Related Measures"]
        self.assertEqual(1, len(matches))
        self.assertEqual(expected, matches[0]["scholarly_or_official_url"])
        curves = [row for row in resources if row["name"] == "Doeblin Curves"]
        self.assertEqual(1, len(curves))
        self.assertEqual("https://doi.org/10.1109/TIT.2026.3678229", curves[0]["scholarly_or_official_url"])
        self.assertEqual("journal article with author manuscript", curves[0]["resource_type"])
        bib_path = PROJECT_PAPER / "references.bib"
        if bib_path.exists():
            _, fields = parse_bib(bib_path.read_text(encoding="utf-8"))["makur2024"]
            self.assertEqual("10.1109/TIT.2024.3367856", fields["doi"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceAuditTest)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    counts = Counter(row["calibration_category"] for row in ReferenceAuditTest.rows)
    payload = {
        "schema": "reference-audit-result-v1",
        "successful": outcome.wasSuccessful(),
        "bibliography_entries": len(ReferenceAuditTest.rows),
        "canonical_urls": len({row["canonical_url"] for row in ReferenceAuditTest.rows}),
        "full_text_calibration": sum(row["full_text_calibration"] == "yes" for row in ReferenceAuditTest.rows),
        "same_venue_tdsc": counts["same-venue TDSC"],
        "influential": counts["influential field paper"],
        "adjacent_or_theory": counts["adjacent venue/theory"],
        "metadata_only": counts["metadata_only"],
        "project_paper_crosscheck_available": (PROJECT_PAPER / "references.bib").exists() and (PROJECT_PAPER / "main.tex").exists(),
        "scope": "structural and retained-provenance consistency; not a live-Web validator or proof that metadata-only papers were read in full",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
