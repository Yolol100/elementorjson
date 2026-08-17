import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_repo_contracts import validate_repository_contracts


class RepositoryContractTests(unittest.TestCase):
    def test_repository_contracts_match_elementor_runtime_boundaries(self):
        self.assertEqual(validate_repository_contracts(ROOT), [])


if __name__ == "__main__":
    unittest.main()
