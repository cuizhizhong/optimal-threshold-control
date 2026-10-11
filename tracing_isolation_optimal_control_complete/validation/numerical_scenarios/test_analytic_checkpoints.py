"""解析依赖回归测试；不读取或生成优化结果。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import generate_analytic_checkpoints as generator


class AnalyticCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = generator.load_inputs(generator.ROOT / "scenario_inputs.json")
        cls.actual = generator.calculate(cls.inputs)
        cls.saved = json.loads((generator.ROOT / "analytic_checkpoints.json").read_text(encoding="utf-8"))

    def test_independent_calculation_matches_fixture(self):
        generator.compare_fixture(self.actual, self.saved)
        self.assertFalse(self.actual["openocl_executed"])
        self.assertEqual(len(self.actual["cases"]), 6)

    def assert_invalid_parameters(self, parameters):
        with self.assertRaises(ValueError) as error:
            generator.Geometry(parameters)
        self.assertEqual(
            str(error.exception),
            "Model parameters must be finite and satisfy 0 < p < 1, c > 0, "
            "gamma > 0, and 0 < K < 1",
        )

    def test_nonfinite_parameters_are_rejected(self):
        for field in ("p", "c", "gamma", "K"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(self.inputs["parameters"])
                    bad[field] = value
                    self.assert_invalid_parameters(bad)

    def test_probability_and_capacity_bounds_are_rejected(self):
        for field in ("p", "K"):
            for value in (-0.1, 0, 1, 1.1):
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(self.inputs["parameters"])
                    bad[field] = value
                    self.assert_invalid_parameters(bad)

    def test_nonpositive_rates_are_rejected(self):
        for field in ("c", "gamma"):
            for value in (-0.1, 0):
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(self.inputs["parameters"])
                    bad[field] = value
                    self.assert_invalid_parameters(bad)

    def test_reordered_fixture_matches_by_case_id(self):
        reordered = copy.deepcopy(self.saved)
        reordered["cases"].reverse()
        generator.compare_fixture(self.actual, reordered)

    def test_reordered_inputs_have_same_calculation(self):
        reordered = copy.deepcopy(self.inputs)
        reordered["cases"].reverse()
        generator.compare_fixture(generator.calculate(reordered), self.saved)

    def test_duplicated_case_id_is_rejected(self):
        bad = copy.deepcopy(self.saved)
        bad["cases"][1]["case_id"] = bad["cases"][0]["case_id"]
        with self.assertRaisesRegex(ValueError, "Duplicated case_id"):
            generator.compare_fixture(self.actual, bad)

    def test_changed_initial_condition_and_cost_are_rejected(self):
        for field in ("s0", "J_reference"):
            bad = copy.deepcopy(self.saved)
            bad["cases"][0][field] += 1e-5
            with self.assertRaisesRegex(ValueError, "Fixture value differs"):
                generator.compare_fixture(self.actual, bad)

    def test_check_is_read_only_for_reordered_fixture(self):
        with tempfile.TemporaryDirectory(prefix="analytic_fixture_test_", dir=generator.ROOT) as task_dir:
            self.assertEqual(Path(task_dir).resolve().parent, generator.ROOT.resolve())
            path = Path(task_dir) / "fixture.json"
            reordered = copy.deepcopy(self.saved)
            reordered["cases"].reverse()
            path.write_text(json.dumps(reordered), encoding="utf-8")
            before = path.read_bytes()
            run = subprocess.run([sys.executable, str(generator.ROOT / "generate_analytic_checkpoints.py"),
                                  "--check", "--fixture", str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("ANALYTIC_CHECKPOINTS_CHECK_OK", run.stdout)
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
