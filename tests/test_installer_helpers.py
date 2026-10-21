"""Testes dos limites de remoção e do bloqueio de pastas indevidas."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("limpar_cache", PROJECT / "instalador/limpar_cache.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class InstallerHelpersTest(unittest.TestCase):
    def test_cleanup_preserves_documents_and_preferences(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-cache-") as temporary:
            root = Path(temporary)
            (root / "pacote.json").write_text('{"produto":"Ditado"}', encoding="utf-8")
            (root / "transcritor.py").write_text("# teste", encoding="utf-8")
            (root / "ocorrencia.txt").write_text("Texto que deve permanecer", encoding="utf-8")
            cache = root / "runtime/Lib/__pycache__"
            cache.mkdir(parents=True)
            (cache / "modulo.pyc").write_bytes(b"cache")
            cleanup.clean(root)
            self.assertFalse(cache.exists())
            self.assertTrue((root / "ocorrencia.txt").is_file())
            self.assertTrue((root / "transcritor.py").is_file())

    def test_cleanup_rejects_unmarked_directory(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-other-") as temporary:
            root = Path(temporary)
            (root / "outro.txt").write_text("preservar", encoding="utf-8")
            with self.assertRaises(ValueError):
                cleanup.clean(root)
            self.assertTrue((root / "outro.txt").exists())

    def test_setup_guard_rejects_foreign_directory(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-guard-") as temporary:
            root = Path(temporary)
            (root / "outro.txt").write_text("preservar", encoding="utf-8")
            result = subprocess.run([
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(PROJECT / "instalador/verificar_em_uso.ps1"), "-Destino", str(root),
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 30, result.stderr)
            self.assertTrue((root / "outro.txt").exists())

    def test_setup_guard_allows_fresh_destination(self):
        with tempfile.TemporaryDirectory(prefix="Ditado-new-") as temporary:
            root = Path(temporary) / "aplicativo"
            result = subprocess.run([
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(PROJECT / "instalador/verificar_em_uso.ps1"), "-Destino", str(root),
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
