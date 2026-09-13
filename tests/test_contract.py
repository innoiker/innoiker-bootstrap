from __future__ import annotations

import unittest

from innoiker_bootstrap.config import build_config, parse_platforms
from innoiker_bootstrap.create import normalize_slug


class ContractTests(unittest.TestCase):
    def test_platforms_are_canonical_and_unique(self) -> None:
        self.assertEqual(parse_platforms(" server, android "), ("android", "server"))

    def test_empty_platforms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_platforms(" , ")

    def test_duplicate_platforms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_platforms("android, android")

    def test_unknown_platforms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_platforms("ios")

    def test_slug_is_stable(self) -> None:
        self.assertEqual(normalize_slug("My Project"), "my-project")


if __name__ == "__main__":
    unittest.main()
