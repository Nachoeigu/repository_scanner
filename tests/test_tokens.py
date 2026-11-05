# tests/test_tokens.py
"""Tests de la estimación de tokens."""

import unittest

import tokens


class TokensTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(tokens.estimate_tokens(''), 0)

    def test_fallback_ratio_when_no_tiktoken(self):
        old_enc, old_failed = tokens._encoder, tokens._tiktoken_failed
        tokens._encoder, tokens._tiktoken_failed = None, True
        try:
            self.assertEqual(tokens.estimate_tokens('a' * 40), 10)
        finally:
            tokens._encoder, tokens._tiktoken_failed = old_enc, old_failed

    def test_returns_positive_int(self):
        self.assertIsInstance(tokens.estimate_tokens('hola mundo'), int)
        self.assertGreater(tokens.estimate_tokens('hola mundo'), 0)


if __name__ == '__main__':
    unittest.main()
