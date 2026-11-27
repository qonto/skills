import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_simulator.py"
START = '<script id="sim-data" type="application/json">'
END = '</script>'


class RenderSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Safe simulator renderer missing")
        spec = importlib.util.spec_from_file_location("render_simulator", SCRIPT)
        self.renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.renderer)

    def test_untrusted_text_cannot_end_json_script(self):
        data = {"name": '</ScRiPt><script>alert("test")</script>', "note": '<!-- & café'}
        html = self.renderer.render(data)
        embedded = html.split(START, 1)[1].split(END, 1)[0]
        self.assertNotIn('<', embedded)
        self.assertEqual(json.loads(embedded), data)

    def test_template_outside_data_block_is_unchanged(self):
        template = (ROOT / "assets" / "cash-simulator.html").read_text(encoding="utf-8")
        prefix, rest = template.split(START, 1)
        _, suffix = rest.split(END, 1)
        html = self.renderer.render({"org": "Example"})
        self.assertTrue(html.startswith(prefix + START))
        self.assertTrue(html.endswith(END + suffix))

    def test_cli_renders_utf8_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "assessment.json"
            output = Path(tmp) / "simulator.html"
            source.write_text(json.dumps({"org": "Éxample </script>"}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            embedded = output.read_text(encoding="utf-8").split(START, 1)[1].split(END, 1)[0]
            self.assertEqual(json.loads(embedded), {"org": "Éxample </script>"})

    def test_cli_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "assessment.json"
            output = Path(tmp) / "simulator.html"
            source.write_text('{}', encoding="utf-8")
            output.write_text('keep user work', encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), 'keep user work')


if __name__ == "__main__":
    unittest.main()
