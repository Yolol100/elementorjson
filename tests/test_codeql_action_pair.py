"""Guard CodeQL's runtime pin pairing: init/analyze must update together."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodeQLActionPairTests(unittest.TestCase):
    def test_init_and_analyze_use_same_full_sha_and_version(self):
        workflow = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
        matches = re.findall(
            r"^\s*uses: github/codeql-action/(init|analyze)@([a-f0-9]{40}) # (v\d+\.\d+\.\d+)$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(2, len(matches), "CodeQL must have exactly init and analyze pins")
        pins = {name: (sha, version) for name, sha, version in matches}
        self.assertEqual({"init", "analyze"}, set(pins))
        self.assertEqual(pins["init"], pins["analyze"], "Mismatched CodeQL versions break CI")

    def test_dependabot_groups_codeql_actions(self):
        settings = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        self.assertIn('package-ecosystem: "github-actions"', settings)
        self.assertRegex(settings, r"(?m)^\s+codeql-actions:\s*$")
        self.assertIn('"github/codeql-action/*"', settings)


if __name__ == "__main__":
    unittest.main()
