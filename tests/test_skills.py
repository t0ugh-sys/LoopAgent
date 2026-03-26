from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401

from loop_agent.skills import SkillLoader, skill_metadata


class SkillsTests(unittest.TestCase):
    def test_should_read_skill_metadata_from_frontmatter(self) -> None:
        meta = skill_metadata('files')
        self.assertIsNotNone(meta)
        self.assertEqual(meta['name'], 'files')
        self.assertEqual(meta['description'], 'Read, write, patch, and search files')

    def test_should_load_skill_body_from_skill_md(self) -> None:
        loader = SkillLoader()
        self.assertTrue(loader.load('commands'))
        body = loader.load_body('commands')
        self.assertIsNotNone(body)
        self.assertIn('Provided tools:', body)
        self.assertIn('run_command', body)


if __name__ == '__main__':
    unittest.main()
