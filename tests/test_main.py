import click
from click.testing import CliRunner
import tempfile
from jf.__main__ import main


def test_main():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".json") as tmpfile:
        tmpfile.write(b'[{"a": "myvalue"}]') and True
        tmpfile.flush()
        result = runner.invoke(
            main, [".a", tmpfile.name, "--import", "hashlib", "--import_from", "extras"]
        )
        assert result.exit_code == 0, repr((result.exit_code, result.output))
        assert result.output == '"myvalue"\n', repr(result.output)
