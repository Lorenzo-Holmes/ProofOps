from __future__ import annotations

import unittest

from proofops.catalog import AGENTS, SKILLS, validate_catalog


class SkillCatalogTests(unittest.TestCase):
    def test_catalog_contains_six_distinct_agent_roles(self) -> None:
        self.assertEqual(len(AGENTS), 6)
        self.assertEqual(len({agent.id for agent in AGENTS}), 6)
        self.assertTrue(all(agent.security_boundary for agent in AGENTS))

    def test_each_skill_has_competition_required_contract_fields(self) -> None:
        errors = validate_catalog()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(len(SKILLS), 7)

        for skill in SKILLS:
            self.assertTrue(skill.inputs)
            self.assertTrue(skill.outputs)
            self.assertTrue(skill.invocation_conditions)
            self.assertTrue(skill.failure_handling)
            self.assertTrue(skill.security_boundary)
            self.assertTrue(skill.reuse_value)


if __name__ == "__main__":
    unittest.main()

