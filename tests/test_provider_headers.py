from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401

from anvil.llm.providers import parse_provider_headers


class ProviderHeadersTests(unittest.TestCase):
    def test_should_parse_provider_headers(self) -> None:
        headers = parse_provider_headers(['x-foo:bar', 'x-baz: qux'])
        self.assertEqual(headers['x-foo'], 'bar')
        self.assertEqual(headers['x-baz'], 'qux')

    def test_should_reject_invalid_header_format(self) -> None:
        with self.assertRaises(ValueError):
            parse_provider_headers(['invalid'])


if __name__ == '__main__':
    unittest.main()

