import unittest
from sae_portfolio_scheduler_v3 import plan_sources


def item(pid, host, n, known=0, **kwargs):
    return dict(project_id=pid, origin=host, url=f'https://{host}/{pid}',
                project_match_confirmed=True, robots_verified=True,
                terms_allow_automation=True,
                source_units=[dict(source_building_code='B1', source_unit_code=str(k)) for k in range(n)],
                master_unit_keys=[dict(source_building_code='B1', source_unit_code=str(k)) for k in range(known)],
                **kwargs)


class FrontierTests(unittest.TestCase):
    def test_identified_inventory_beats_large_marketing_only(self):
        marketing = item('PRJ-000001', 'market.sa', 0, marketing_total=20000)
        source = item('PRJ-000002', 'feed.sa', 400, known=100, marketing_total=1)
        out = plan_sources([marketing, source], {})
        self.assertEqual(out['queue'][0]['project_id'], 'PRJ-000002')
        self.assertEqual(out['queue'][0]['unmatched_source_keys'], 300)
        self.assertEqual(out['summary']['canonical_writes'], 0)

    def test_no_repeat_exhausted_source_unchanged(self):
        a = item('PRJ-000003', 'feed.sa', 20, 20, source_fingerprint='sha-abc')
        out = plan_sources([a], {'PRJ-000003|https://feed.sa/PRJ-000003': {'source_fingerprint': 'sha-abc'}})
        self.assertEqual(out['summary']['queued'], 0)
        self.assertEqual(out['skipped'][0]['reason'], 'SOURCE_UNCHANGED_NO_UNIT_DELTA')

    def test_failclosed_permission_and_missing_building(self):
        a = item('PRJ-000004', 'blocked.sa', 5)
        a['terms_allow_automation'] = False
        b = item('PRJ-000005', 'unsafe.sa', 1)
        b['source_units'][0].pop('source_building_code')
        out = plan_sources([a, b], {})
        self.assertEqual({x['reason'] for x in out['skipped']},
                         {'ACCESS_PERMISSION_UNVERIFIED', 'SOURCE_IDENTITY_COLLISION_OR_MISSING'})

    def test_project_name_never_enough(self):
        a = item('PRJ-000006', 'feed.sa', 100)
        a['project_match_confirmed'] = False
        out = plan_sources([a], {})
        self.assertEqual(out['summary']['queued'], 0)

    def test_dedup_collision_is_failclosed(self):
        a = item('PRJ-000007', 'feed.sa', 2)
        a['source_units'][1]['source_unit_code'] = '0'
        out = plan_sources([a], {})
        self.assertEqual(out['skipped'][0]['reason'], 'SOURCE_IDENTITY_COLLISION_OR_MISSING')

    def test_round_robin_across_origins(self):
        items = [item(f'PRJ-{i:06d}', 'x.sa', 2) for i in range(10, 14)]
        items += [item('PRJ-000020', 'y.sa', 1)]
        out = plan_sources(items, {}, max_publishers=2, max_items=3)
        self.assertEqual([x['origin'] for x in out['queue']], ['x.sa', 'y.sa', 'x.sa'])

    def test_full_registered_portfolio_not_silently_capped(self):
        # 151 independent, exact matched original publishers are all scheduled,
        # not silently truncated to the previous 14 origins / 80 items.
        candidates = [
            item(f'PRJ-{i:06d}', f'publisher-{i:03d}.sa', 1)
            for i in range(1, 152)
        ]
        out = plan_sources(candidates, {})
        self.assertEqual(out['summary']['queued'], 151)
        self.assertEqual(out['summary']['origins'], 151)
        self.assertEqual(out['summary']['itemized_unmatched_candidates'], 151)
        self.assertEqual(out['summary']['canonical_writes'], 0)

    def test_explicit_small_budget_still_respected(self):
        candidates = [
            item(f'PRJ-{i:06d}', f'publisher-{i:03d}.sa', 1)
            for i in range(1, 12)
        ]
        out = plan_sources(candidates, {}, max_publishers=3, max_items=2)
        self.assertEqual(out['summary']['queued'], 2)
        self.assertEqual(out['summary']['origins'], 2)

    def test_default_portfolio_still_does_not_bypass_robots_or_terms(self):
        candidates = [
            item(f'PRJ-{i:06d}', f'publisher-{i:03d}.sa', 1)
            for i in range(1, 152)
        ]
        candidates[20]['robots_verified'] = False
        candidates[40]['terms_allow_automation'] = False
        out = plan_sources(candidates, {})
        self.assertEqual(out['summary']['queued'], 149)
        self.assertEqual(len(out['skipped']), 2)

    def test_429_block_unchanged(self):
        a = item('PRJ-000021', 'feed.sa', 300)
        out = plan_sources([a], {'PRJ-000021|https://feed.sa/PRJ-000021': {'stop_429': True}})
        self.assertEqual(out['skipped'][0]['reason'], 'SOURCE_BLOCKED')

    def test_different_buildings_distinct(self):
        a = item('PRJ-000022', 'feed.sa', 2)
        a['source_units'][1]['source_unit_code'] = '0'
        a['source_units'][1]['source_building_code'] = 'B2'
        out = plan_sources([a], {})
        self.assertEqual(out['summary']['itemized_unmatched_candidates'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
