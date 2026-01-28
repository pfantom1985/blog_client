from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """
    Записывает JSON в UTF-8.
    indent делает файл “человекочитаемым”. [web:577]
    ensure_ascii=False оставляет Unicode-символы читаемыми. [web:573]
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=indent,
        )
        f.write("\n")  # удобно в терминале и git diff


def read_json(path: str | Path) -> Any:
    """
    Читает JSON из UTF-8 и возвращает Python-объект (dict/list/str/...). [web:579]
    json.JSONDecodeError пробрасываем наверх — cli.py красиво объяснит пользователю.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
