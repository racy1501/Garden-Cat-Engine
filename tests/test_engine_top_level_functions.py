import ast
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_game_engine_has_no_unexpected_top_level_function_overrides():
    source = (PROJECT_ROOT / "game_engine.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    names = [
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    duplicates = {name: count for name, count in Counter(names).items() if count > 1}

    assert duplicates == {"normalize_state": 2}
