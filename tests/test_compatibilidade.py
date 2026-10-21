"""Migração de preferências e comunicação entre versões do aplicativo."""
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from compatibilidade import LEGACY_DATA_DIRECTORY, migrate_preferences
from integracao_windows import SingleInstance


class CompatibilityTest(unittest.TestCase):
    def test_migrate_preserves_legacy_preferences_and_original_file(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-migracao-") as temporary:
            root = Path(temporary)
            original = root / LEGACY_DATA_DIRECTORY / "config.json"
            original.parent.mkdir()
            content = json.dumps({"sounds": False, "microphone": "Microfone preferido"})
            original.write_text(content, encoding="utf-8")
            destination = root / "Ditado"
            migrate_preferences(destination)
            self.assertEqual((destination / "config.json").read_text(encoding="utf-8"), content)
            self.assertEqual(original.read_text(encoding="utf-8"), content)

    def test_migrate_never_overwrites_current_preferences(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-config-") as temporary:
            root = Path(temporary)
            source = root / LEGACY_DATA_DIRECTORY
            source.mkdir()
            (source / "config.json").write_text('{"sounds":false}', encoding="utf-8")
            destination = root / "Ditado"
            destination.mkdir()
            current = destination / "config.json"
            current.write_text('{"sounds":true}', encoding="utf-8")
            migrate_preferences(destination)
            self.assertEqual(current.read_text(encoding="utf-8"), '{"sounds":true}')

    def test_migrate_ignores_invalid_legacy_configuration(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-invalid-") as temporary:
            root = Path(temporary)
            source = root / LEGACY_DATA_DIRECTORY
            source.mkdir()
            for content in ("{invalido", "[]"):
                (source / "config.json").write_text(content, encoding="utf-8")
                migrate_preferences(root / "Ditado")
                self.assertFalse((root / "Ditado/config.json").exists())

    def test_new_instance_can_activate_running_legacy_instance(self):
        prefix = "Local\\DitadoTeste" + uuid4().hex
        names = (prefix + "Novo", prefix + "Anterior")
        previous = SingleInstance(names=(names[1],))
        current = None
        try:
            self.assertFalse(previous.already_running)
            current = SingleInstance(names=names)
            self.assertTrue(current.already_running)
            current.request_show()
            self.assertTrue(previous.show_requested())
        finally:
            if current:
                current.close()
            previous.close()

    def test_legacy_instance_cannot_duplicate_new_running_instance(self):
        prefix = "Local\\DitadoTeste" + uuid4().hex
        names = (prefix + "Novo", prefix + "Anterior")
        current = SingleInstance(names=names)
        previous = None
        try:
            self.assertFalse(current.already_running)
            previous = SingleInstance(names=(names[1],))
            self.assertTrue(previous.already_running)
            previous.request_show()
            self.assertTrue(current.show_requested())
        finally:
            if previous:
                previous.close()
            current.close()


if __name__ == "__main__":
    unittest.main()
