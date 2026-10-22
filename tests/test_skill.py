from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pick_names
import check_environment


class NameTests(unittest.TestCase):
    def test_pool_matches_tool_name_contract(self):
        self.assertEqual(len(pick_names.NAMES), len(set(pick_names.NAMES)))
        for name in pick_names.NAMES:
            self.assertRegex(name, r"^[a-z]+$")

    def test_full_pool_unique(self):
        self.assertCountEqual(pick_names.pick_names(len(pick_names.NAMES)), pick_names.NAMES)

    def test_excluded_names_cannot_be_selected(self):
        excluded = pick_names.NAMES[:3]
        result = pick_names.pick_names(len(pick_names.NAMES) - 3, excluded)
        self.assertTrue(set(result).isdisjoint(excluded))
        self.assertEqual(len(result), len(set(result)))

    def test_repeated_and_unknown_exclusions(self):
        self.assertNotIn("curie", pick_names.pick_names(3, ["curie", "curie", "unknown"]))

    def test_invalid_counts_and_exhaustion(self):
        for count, exclusions in ((0, []), (-1, []), (len(pick_names.NAMES) + 1, []), (1, pick_names.NAMES)):
            with self.subTest(count=count), self.assertRaises(ValueError):
                pick_names.pick_names(count, exclusions)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/pick_names.py"), *args], text=True, capture_output=True)

    def test_cli_json(self):
        result = self.cli("--count", "2", "--exclude", "curie", "--exclude", "newton")
        self.assertEqual(result.returncode, 0, result.stderr)
        names = json.loads(result.stdout)
        self.assertEqual(len(set(names)), 2)
        self.assertTrue(set(names).isdisjoint({"curie", "newton"}))
        self.assertEqual(result.stderr, "")

    def test_cli_bad_input(self):
        for args in (("--count", "0"), ("--count", "100"), ("--count", "bad"), ()):
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error", result.stderr)

    def test_fresh_copy_path_with_spaces_and_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory) / "new user" / "dispatch-scientist-subagents"
            install.mkdir(parents=True)
            for relative in ("SKILL.md", "agents", "scripts", "README.md"):
                source = ROOT / relative
                if source.is_dir():
                    shutil.copytree(source, install / relative, ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    shutil.copy2(source, install / relative)
            result = subprocess.run([sys.executable, str(install / "scripts/pick_names.py"), "--count", "2"], cwd=directory, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(set(json.loads(result.stdout))), 2)


class EnvironmentTests(unittest.TestCase):
    def test_feature_output_supports_multiword_status(self):
        result = check_environment.inspect_features("multi_agent stable true\nmulti_agent_v2 under development false\ninvalid\n")
        self.assertEqual(result, {"multi_agent": True, "multi_agent_v2": False})

    def run_check(self, config, features):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "config.toml").write_text(config, encoding="utf-8")
            output = io.StringIO()
            def cli(_executable, *args):
                return "codex-cli test" if args == ("--version",) else features
            with mock.patch.dict("os.environ", {"CODEX_HOME": directory}), mock.patch.object(check_environment.shutil, "which", return_value="codex"), mock.patch.object(check_environment, "run_cli", side_effect=cli), contextlib.redirect_stdout(output):
                result = check_environment.main()
            return result, output.getvalue()

    def test_missing_v2_returns_actionable_failure(self):
        code, output = self.run_check("", "multi_agent stable true\nmulti_agent_v2 stable false")
        self.assertEqual(code, 1)
        self.assertIn("codex features enable multi_agent_v2", output)

    def test_enabled_flags_and_valid_config_pass_static_checks(self):
        code, output = self.run_check("[agents]\nenabled = true\nmax_concurrent_threads_per_session = 3\n", "multi_agent stable true\nmulti_agent_v2 stable true")
        self.assertEqual(code, 0)
        self.assertIn("do not inspect live model tools", output)

    def test_disabled_agents_and_insufficient_slots_fail(self):
        for config in ("[agents]\nenabled=false", "[agents]\nmax_concurrent_threads_per_session=1"):
            code, _ = self.run_check(config, "multi_agent stable true\nmulti_agent_v2 stable true")
            self.assertEqual(code, 1)

    def test_disabled_skill_fails(self):
        skill_path = json.dumps(str(ROOT / "SKILL.md"))
        code, _ = self.run_check(f"[[skills.config]]\npath={skill_path}\nenabled=false", "multi_agent stable true\nmulti_agent_v2 stable true")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
