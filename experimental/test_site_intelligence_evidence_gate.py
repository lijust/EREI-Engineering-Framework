#!/usr/bin/env python3
"""SAE site-intelligence negative/positive evidence unit tests."""
import unittest
from site_intelligence_evidence_gate import classify_table,classify_xhr_endpoint,inspect_report

class SourceEvidenceGateTests(unittest.TestCase):
    def test_google_maps_shortcuts_never_unit_inventory(self):
        t=classify_table([["Keystroke","Action"]],[["←","Move left"],["+","Zoom in"]])
        self.assertEqual(t["class"],"NON_PROPERTY_ACCESSIBILITY_TABLE")
        self.assertEqual(t["accepted"],0)

    def test_row_count_does_not_create_units(self):
        t=classify_table([["Available","Area"]],[["10","130"] for _ in range(1000)])
        self.assertEqual(t["accepted"],0)
        self.assertEqual(t["class"],"TABLE_NEEDS_IDENTITY_FIELDS")

    def test_marketing_total_never_units(self):
        s=inspect_report({"sites":[{"key":"marvela","url":"https://www.rafal.com.sa/communities/marvela",
            "published_aggregate_not_individual":594,"static":{"public_links":[]},
            "browser":{"xhr":[]}}]})
        self.assertEqual(s["new_units_committed"],0)
        self.assertEqual(s["sites"][0]["validated_new_physical_units"],0)

    def test_google_maps_xhr_rejected_even_when_json_array_has_items(self):
        res=classify_xhr_endpoint({"url":"https://maps.googleapis.com/$rpc/mapsjs",
                   "shape":[{"path":"$","array_length":10,"first_item_fields":["unitCode","projectId"]}]})
        self.assertEqual(res["class"],"THIRD_PARTY_OR_TELEMETRY_EXCLUDED")

    def test_tag_endpoint_rejected(self):
        res=classify_xhr_endpoint({"url":"https://darco.com.sa/api/public/google-tags/active",
          "shape":[{"path":"$","array_length":1,"first_item_fields":["unitCode","projectId"]}]})
        self.assertEqual(res["accepted"],0)

    def test_strong_firstparty_unit_array_provisional_only(self):
        res=classify_xhr_endpoint({"url":"https://developer.example/api/units",
             "shape":[{"path":"$","array_length":900,
                "first_item_fields":["unitCode","projectId","area","price"]}]})
        self.assertEqual(res["class"],"CANDIDATE_FIRSTPARTY_UNIT_API_NEEDS_ITEM_VALIDATION")
        self.assertEqual(res["accepted"],0)

    def test_source_table_code_and_building_needs_row_validation(self):
        r=classify_table([["Project","Building","Unit Number","Area"]],
             [["Marvela","B1","101","155"],["Marvela","B1","102","155"]])
        self.assertEqual(r["class"],"POTENTIAL_ITEMIZED_TABLE_REQUIRES_ROW_VERIFICATION")
        self.assertEqual(r["accepted"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
