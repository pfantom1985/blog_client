# blog_client

Небольшой CLI‑клиент для работы с “блоговым” API JSONPlaceholder: скачивает посты и комментарии, сохраняет данные в JSON и умеет считать простую статистику.

## Требования
- Python 3.12+ (подойдёт и 3.11+, если зависимости совместимы)

## Установка (рекомендуется)
Из корня проекта:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Использование

Скачать посты (без комментариев):
```bash
python -m blog_client posts --limit 10 --out posts.json
```

Скачать один пост и его комментарии:
```bash
python -m blog_client post 1 --out post_1.json
```

Скачать все посты + комментарии в один файл:
```bash
python -m blog_client export --limit 10 --out export.json
```

Посчитать статистику по export.json:
```bash
python -m blog_client stats --out export.json
```

Проверка ретраев:
```bash
python -m blog_client selfcheck
```

Selfcheck с указанием base URL:
```bash
python -m blog_client selfcheck --selfcheck-url https://httpbin.dev
```

## Структура проекта (модули)

- `blog_client/cli.py` — CLI: парсинг аргументов и команды `posts`, `post`, `export`, `stats`, `selfcheck`.  
- `blog_client/client.py` — HTTP‑клиент: запросы к API, таймауты/ретраи, обработка ошибок, преобразование ответов в модели.  
- `blog_client/models.py` — Pydantic‑модели (`Post`, `Comment`, `PostWithComments`) и адаптеры для списков.  
- `blog_client/storage.py` — чтение/запись JSON файлов (`read_json`/`write_json`).  
- `blog_client/utils.py` — служебные функции (например, `dump_jsonable`) и коды завершения CLI.
