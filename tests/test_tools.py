from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

import _bootstrap  # noqa: F401

from loop_agent.agent_protocol import ToolCall
from loop_agent.tools import ToolContext, build_default_tools, execute_tool_call


class ToolsTests(unittest.TestCase):
    def test_should_apply_patch_update_file(self) -> None:
        tmp_dir = Path('tests/.tmp') / f'tools-{uuid.uuid4().hex}'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        target = tmp_dir / 'README.md'
        target.write_text('hello\nworld\n', encoding='utf-8')
        try:
            patch = '\n'.join(
                [
                    '*** Begin Patch',
                    '*** Update File: README.md',
                    '@@',
                    '-hello',
                    '+hi',
                    '*** End Patch',
                ]
            )
            call = ToolCall(id='call_1', name='apply_patch', arguments={'patch': patch})
            result = execute_tool_call(ToolContext(workspace_root=tmp_dir), call, build_default_tools())
            self.assertTrue(result.ok, msg=result.error or '')
            self.assertIn('README.md', result.output)
            self.assertEqual(target.read_text(encoding='utf-8'), 'hi\nworld\n')
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_should_reject_patch_outside_workspace(self) -> None:
        tmp_dir = Path('tests/.tmp') / f'tools-{uuid.uuid4().hex}'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            patch = '\n'.join(
                [
                    '*** Begin Patch',
                    '*** Add File: ../escape.txt',
                    '+x',
                    '*** End Patch',
                ]
            )
            call = ToolCall(id='call_1', name='apply_patch', arguments={'patch': patch})
            result = execute_tool_call(ToolContext(workspace_root=tmp_dir), call, build_default_tools())
            self.assertFalse(result.ok)
            self.assertIn('workspace', result.error or '')
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
