import json
from blog_client.storage import read_json, write_json

def test_write_then_read_roundtrip(tmp_path):
    path = tmp_path / "data.json"
    payload = {"a": 1, "b": [1, 2, 3], "c": "Привет"}

    write_json(path, payload)

    assert read_json(path) == payload

def test_read_invalid_json_raises(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json", encoding="utf-8")

    try:
        read_json(path)
        assert False, "Expected JSONDecodeError"
    except json.JSONDecodeError:
        assert True
