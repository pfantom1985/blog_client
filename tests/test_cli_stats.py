import argparse
from blog_client.cli import cmd_stats
from blog_client.utils import EXIT_INPUT_ERROR

def test_stats_file_not_found(tmp_path, capsys):
    args = argparse.Namespace(out=str(tmp_path / "no_such_file.json"))

    code = cmd_stats(args)
    captured = capsys.readouterr()

    assert code == EXIT_INPUT_ERROR
    assert "Файл не найден" in captured.out
