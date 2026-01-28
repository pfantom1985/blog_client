from __future__ import annotations

from typing import Any

EXIT_OK = 0
EXIT_RUNTIME_ERROR = 1   # сеть/HTTP/валидация ответа API
EXIT_INPUT_ERROR = 2     # проблемы входного файла (stats)

def dump_jsonable(obj: Any) -> Any:
    """
    Приводит Pydantic-модели и вложенные структуры к JSON-совместимым типам.
    Pydantic v2 рекомендует model_dump(mode="json") для JSON-friendly вывода. [web:528]
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")  # ключевое место
    if isinstance(obj, list):
        return [dump_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: dump_jsonable(v) for k, v in obj.items()}
    return obj
