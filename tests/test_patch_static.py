from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LuminaDesktopPatchTests(unittest.TestCase):
    def test_existing_chat_and_voice_routes_are_reused(self):
        source = (ROOT / "ui/src/desktop/DesktopCompanion.tsx").read_text(encoding="utf-8")
        self.assertIn("'/api/chat'", source)
        self.assertIn("'/api/tts/speak'", source)
        self.assertIn("use_memory: true", source)

    def test_agent_routes_are_allowlisted_in_main_process(self):
        source = (ROOT / "ui/desktop/main.cjs").read_text(encoding="utf-8")
        self.assertIn("'/v1/apps'", source)
        self.assertIn("'/v1/apps/open'", source)
        self.assertIn("/health", source)
        self.assertIn("shell: false", source) if "shell: false" in source else self.assertIn("safeApiPath", source)

    def test_renderer_does_not_receive_node_integration(self):
        source = (ROOT / "ui/desktop/main.cjs").read_text(encoding="utf-8")
        self.assertIn("contextIsolation: true", source)
        self.assertIn("nodeIntegration: false", source)
        self.assertIn("sandbox: true", source)

    def test_original_web_app_remains_default(self):
        source = (ROOT / "ui/src/main.tsx").read_text(encoding="utf-8")
        self.assertIn('get("desktop") === "1"', source)
        self.assertIn("<App />", source)
        self.assertIn("<DesktopCompanion />", source)


if __name__ == "__main__":
    unittest.main()
