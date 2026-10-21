"""Compatibilidade com instalações anteriores à mudança do nome para Ditado."""
import json
from pathlib import Path

# Os identificadores antigos permitem atualizar sem perder as preferências
# nem abrir duas cópias que disputem o mesmo atalho global.
LEGACY_DATA_DIRECTORY = "WhisperDitado"
INSTANCE_NAMES = ("Local\\DitadoV2", "Local\\WhisperDitadoV2")


def migrate_preferences(destination: Path):
    target = destination / "config.json"
    if target.exists():
        return
    source = destination.parent / LEGACY_DATA_DIRECTORY / "config.json"
    try:
        content = source.read_text(encoding="utf-8")
        if not isinstance(json.loads(content), dict):
            return
        destination.mkdir(parents=True, exist_ok=True)
        # Não substitui uma configuração que outra instância acabou de salvar.
        with target.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except (OSError, ValueError):
        pass
