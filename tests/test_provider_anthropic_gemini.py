from __future__ import annotations

import argparse
import os
import unittest

import _bootstrap  # noqa: F401

from loop_agent.llm.providers import build_invoke_from_args


class ProviderAnthropicTests(unittest.TestCase):
    def test_should_build_anthropic_invoke(self) -> None:
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        try:
            args = argparse.Namespace(
                provider='anthropic',
                model='claude-3-opus-20240229',
                api_key_env='ANTHROPIC_API_KEY',
                temperature=0.2,
                provider_timeout_s=30.0,
                max_retries=2,
                retry_backoff_s=1.0,
                retry_http_code=[],
            )
            invoke = build_invoke_from_args(args)
            # Just verify it creates successfully, actual API call would need key
            self.assertIsNotNone(invoke)
        finally:
            os.environ.pop('ANTHROPIC_API_KEY', None)

    def test_should_raise_when_anthropic_provider_without_key(self) -> None:
        backup = os.environ.pop('ANTHROPIC_API_KEY', None)
        try:
            args = argparse.Namespace(
                provider='anthropic',
                model='claude-3-opus-20240229',
                api_key_env='ANTHROPIC_API_KEY',
                temperature=0.2,
                provider_timeout_s=30.0,
                max_retries=2,
                retry_backoff_s=1.0,
                retry_http_code=[],
            )
            with self.assertRaises(ValueError):
                build_invoke_from_args(args)
        finally:
            if backup is not None:
                os.environ['ANTHROPIC_API_KEY'] = backup


class ProviderGeminiTests(unittest.TestCase):
    def test_should_build_gemini_invoke(self) -> None:
        os.environ['GEMINI_API_KEY'] = 'test-key'
        try:
            args = argparse.Namespace(
                provider='gemini',
                model='gemini-pro',
                api_key_env='GEMINI_API_KEY',
                temperature=0.2,
                provider_timeout_s=30.0,
                max_retries=2,
                retry_backoff_s=1.0,
                retry_http_code=[],
            )
            invoke = build_invoke_from_args(args)
            # Just verify it creates successfully, actual API call would need key
            self.assertIsNotNone(invoke)
        finally:
            os.environ.pop('GEMINI_API_KEY', None)

    def test_should_raise_when_gemini_provider_without_key(self) -> None:
        backup = os.environ.pop('GEMINI_API_KEY', None)
        try:
            args = argparse.Namespace(
                provider='gemini',
                model='gemini-pro',
                api_key_env='GEMINI_API_KEY',
                temperature=0.2,
                provider_timeout_s=30.0,
                max_retries=2,
                retry_backoff_s=1.0,
                retry_http_code=[],
            )
            with self.assertRaises(ValueError):
                build_invoke_from_args(args)
        finally:
            if backup is not None:
                os.environ['GEMINI_API_KEY'] = backup


if __name__ == '__main__':
    unittest.main()
