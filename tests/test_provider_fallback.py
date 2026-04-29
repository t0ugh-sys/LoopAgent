from __future__ import annotations

import argparse
import os
import unittest

import _bootstrap  # noqa: F401

from anvil.llm.providers import build_invoke_from_args


class ProviderFallbackTests(unittest.TestCase):
    def test_should_build_mock_invoke_with_fallback_args(self) -> None:
        args = argparse.Namespace(
            provider='mock',
            model='m1',
            fallback_model=['m2'],
            base_url='',
            wire_api='chat_completions',
            api_key_env='OPENAI_API_KEY',
            temperature=0.2,
            provider_timeout_s=30.0,
            provider_debug=False,
            provider_header=[],
            max_retries=2,
            retry_backoff_s=1.0,
            retry_http_code=[],
        )
        invoke = build_invoke_from_args(args)
        output = invoke('x')
        self.assertIn('"done"', output)

    def test_should_raise_when_openai_provider_without_key(self) -> None:
        backup = os.environ.pop('OPENAI_API_KEY', None)
        try:
            args = argparse.Namespace(
                provider='openai_compatible',
                model='m1',
                fallback_model=[],
                base_url='https://api.example.com/v1',
                wire_api='responses',
                api_key_env='OPENAI_API_KEY',
                temperature=0.2,
                provider_timeout_s=30.0,
                provider_debug=False,
                provider_header=[],
                max_retries=2,
                retry_backoff_s=1.0,
                retry_http_code=[],
            )
            with self.assertRaises(ValueError):
                build_invoke_from_args(args)
        finally:
            if backup is not None:
                os.environ['OPENAI_API_KEY'] = backup


if __name__ == '__main__':
    unittest.main()

