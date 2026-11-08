"""Реальные локальные сценарии CLI; файлы каждого запуска изолированы."""

#Этап 5

import ast
import json
import os
import subprocess
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from primitive_db import core
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import parse_command, parse_set, parse_values, parse_where
from primitive_db.utils import load_metadata, load_table_data, save_metadata

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = ROOT / ".venv/bin/database"
WORKSPACE = ROOT / ".test-output/workspaces" / str(time.time_ns())
LOG_DIR = ROOT / ".test-output/logs"


def session(label, commands, directory=WORKSPACE):
    """Запускает установленную команду database и сохраняет настоящий вывод."""
    directory.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(EXECUTABLE)],
        input="\n".join(commands) + "\n",
        text=True,
        capture_output=True,
        cwd=directory,
        timeout=10,
    )
    (LOG_DIR / f"{label}.txt").write_text(
        "INPUT\n"
        + "\n".join(commands)
        + "\n\nSTDOUT\n"
        + result.stdout
        + "\nSTDERR\n"
        + result.stderr
        + f"\nEXIT CODE: {result.returncode}\n",
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert not result.stderr, result.stderr
    assert "Traceback" not in result.stdout
    return result.stdout


def rows(directory=WORKSPACE):
    """Читает итоговый JSON независимо от функций приложения."""
    return json.loads((directory / "data/users.json").read_text(encoding="utf-8"))


def check_persistence_and_crud():
    """Проверяет CRUD, кавычки, несколько процессов и актуальность кэша."""
    output = session(
        "01-create-insert",
        [
            "",
            "list_tables",
            "create_table users name:str age:int is_active:bool",
            'insert into users values ("Sergei", 28, true)',
            'insert into users values ("Anna, where = set", 20, false)',
            'insert into users values ("O\'Brien", -5, true)',
            "select from users",
            "info users",
            "exit",
        ],
    )
    assert "ID:int, name:str, age:int, is_active:bool" in output
    assert "Количество записей: 3" in output
    assert rows() == [
        {"ID": 1, "name": "Sergei", "age": 28, "is_active": True},
        {"ID": 2, "name": "Anna, where = set", "age": 20, "is_active": False},
        {"ID": 3, "name": "O'Brien", "age": -5, "is_active": True},
    ]
    metadata = json.loads((WORKSPACE / "db_meta.json").read_text(encoding="utf-8"))
    assert metadata == {"users": ["ID:int", "name:str", "age:int", "is_active:bool"]}
    output = session(
        "02-read-update-cache",
        [
            "list_tables",
            "select from users where age=28",
            "select from users where age=28",
            'update users set age=29, is_active=false where name="Sergei"',
            "select from users where age=28",
            "select from users where age=29",
            'select from users where name="Anna, where = set"',
            "exit",
        ],
    )
    assert "- users" in output
    assert output.count("Sergei") == 3
    assert rows()[0] == {"ID": 1, "name": "Sergei", "age": 29, "is_active": False}
    output = session(
        "03-delete-cancel",
        [
            "delete from users where ID=2",
            "n",
            "drop_table users",
            "",
            "info users",
            "exit",
        ],
    )
    assert output.count("Операция отменена.") == 2
    assert len(rows()) == 3
    output = session(
        "04-delete-and-id",
        [
            "delete from users where ID=2",
            "y",
            'insert into users values ("New", 30, true)',
            "delete from users where ID=99",
            "y",
            "select from users",
            "exit",
        ],
    )
    assert "Запись с ID=2 успешно удалена" in output
    assert "Запись с ID=4 успешно добавлена" in output
    assert [row["ID"] for row in rows()] == [1, 3, 4]
    assert "Подходящих записей нет." in output
    output = session(
        "05-update-many-and-empty-select",
        [
            "update users set age=40 where is_active=true",
            "select from users where age=40",
            "select from users where ID=999",
            "info users",
            "exit",
        ],
    )
    assert output.count("успешно обновлена") == 2
    assert [row["age"] for row in rows()] == [29, 40, 40]
    assert "Количество записей: 3" in output
    print("PASS: CRUD, повторы select, обновление кэша, ID и чтение в новом процессе")


def check_invalid_commands():
    """Ошибочный ввод должен оставить файлы базы неизменными."""
    previous_meta = (WORKSPACE / "db_meta.json").read_bytes()
    previous_data = (WORKSPACE / "data/users.json").read_bytes()
    invalid_commands = [
        "nonsense",
        "create_table",
        "create_table users name:str",
        "create_table wrong amount:float",
        "create_table wrong x:int x:str",
        "create_table wrong ID:int",
        "create_table ../escape x:int",
        "drop_table missing",
        "info missing",
        "info users extra",
        'insert into missing values ("a")',
        'insert into users values ("a", 1)',
        'insert into users values ("a", true, false)',
        'insert into users values ("a", 1, "true")',
        "insert into users values (a, 1, true)",
        'insert into users values ("a" 1 true)',
        'insert into users values ("a", 1, true,)',
        'insert into users values ("a", 1, true) junk',
        'insert into users values ("unclosed, 1, true)',
        "select from users where missing=1",
        'select from users where age="40"',
        "select from users where age>1",
        "select from users where age=40, ID=3",
        "update users set age=true where ID=1",
        "update users set ID=7 where ID=1",
        "update users set age=1, missing=2 where ID=1",
        "update users set age=1, age=2 where ID=1",
        "update users set age=1",
        "delete from users",
        "delete from users where is_active=1",
        "exit extra",
        "list_tables extra",
        "select",
        "help extra",
    ]
    output = session("06-invalid-commands", [*invalid_commands, "info users", "exit"])
    assert output.count("Ошибка") == len(invalid_commands) - 1
    assert "Функции nonsense нет. Попробуйте снова." in output
    assert "Количество записей: 3" in output
    assert "[y/n]" not in output
    assert (WORKSPACE / "db_meta.json").read_bytes() == previous_meta
    assert (WORKSPACE / "data/users.json").read_bytes() == previous_data
    print(f"PASS: {len(invalid_commands)} ошибочные команды, файлы не изменены")


def check_corrupted_files():
    """Некорректный JSON не должен молча перезаписываться."""
    directory = WORKSPACE / "corrupt"
    directory.mkdir()
    meta_path = directory / "db_meta.json"
    meta_path.write_text("{broken", encoding="utf-8")
    output = session("07-broken-metadata", ["list_tables", "exit"], directory)
    assert "Ошибка валидации" in output
    assert meta_path.read_text(encoding="utf-8") == "{broken"
    meta_path.write_text('{"users":["ID:int","name:str"]}', encoding="utf-8")
    data_dir = directory / "data"
    data_dir.mkdir()
    data_path = data_dir / "users.json"
    for index, invalid_json in enumerate(
        [
            "{broken",
            "{}",
            '[{"ID":1,"name":true}]',
            '[{"ID":1,"name":"a"},{"ID":1,"name":"b"}]',
            '[{"ID":1}]',
        ]
    ):
        data_path.write_text(invalid_json, encoding="utf-8")
        output = session(
            f"08-broken-data-{index}",
            [
                'insert into users values ("new")',
                "select from users",
                "exit",
            ],
            directory,
        )
        assert "Ошибка валидации" in output
        assert data_path.read_text(encoding="utf-8") == invalid_json
    print("PASS: повреждённые JSON, типы, поля и дубли ID не перезаписаны")


def check_functions_and_cache():
    """Проверяет замыкание и отсутствие совместного изменения данных."""
    assert parse_values('("a, b = (where)", +2, false)') == ["a, b = (where)", 2, False]
    assert parse_values(r'("He said \"yes\"", 1)') == ['He said "yes"', 1]
    assert parse_where("name = 'two words'") == {"name": "two words"}
    assert parse_set('age=2, name="x"') == {"age": 2, "name": "x"}
    assert parse_values('("", 1)') == ["", 1]
    assert parse_values("('C:\\', 1)") == ["C:\\", 1]
    assert parse_command("update where set where=1 where where=2") == {
        "command": "update",
        "table": "where",
        "set": {"where": 1},
        "where": {"where": 2},
    }
    calls = []
    cache = create_cacher()

    def calculate():
        """Позволяет независимо сосчитать реальное вычисление."""
        calls.append("called")
        return [1]

    assert cache("same", calculate) == [1]
    assert cache("same", calculate) == [1]
    assert calls == ["called"]
    data = [{"ID": 1, "age": 28}]
    first = core.select(data, {"age": 28})
    first[0]["age"] = 99
    assert data[0]["age"] == 28
    assert core.select(data, {"age": 28}) == [{"ID": 1, "age": 28}]
    data[0]["age"] = 29
    assert core.select(data, {"age": 28}) == []
    assert core.select(data, {"age": 29}) == [{"ID": 1, "age": 29}]
    assert core.select([{"flag": True}], {"flag": 1}) == []
    changed = core.update(data, {"age": 30}, {"ID": 1})
    assert changed[0]["age"] == 30 and data[0]["age"] == 29
    metadata = {}
    assert core.create_table(metadata, "test", ["bad:float"]) is None
    assert metadata == {}
    for error in (KeyError("missing"), ValueError("type"), FileNotFoundError()):

        @handle_db_errors
        def fail():
            """Вызывает проверяемое исключение."""
            raise error

        assert fail() is None
    print("PASS: парсер, кэш-замыкание, независимые копии и декоратор ошибок")


def check_structure_and_io():
    """Сверяет ограничения приложения и JSON-функции из условия."""
    modules = {path.name for path in (ROOT / "src/primitive_db").glob("*.py")}
    assert modules == {
        "__init__.py",
        "main.py",
        "engine.py",
        "core.py",
        "utils.py",
        "parser.py",
        "decorators.py",
        "constants.py",
    }
    assert (ROOT / "src/primitive_db/__init__.py").read_bytes() == b""
    allowed = {"json", "shlex", "time", "os", "prompt", "prettytable", "primitive_db"}
    for path in (ROOT / "src/primitive_db").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            assert not isinstance(node, ast.ClassDef), path
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module.split(".")[0] in allowed
    original_directory = os.getcwd()
    try:
        os.chdir(WORKSPACE)
        assert load_metadata("absent.json") == {}
        assert load_table_data("absent") == []
        save_metadata("test_meta.json", {"РусскаяТаблица": ["ID:int"]})
        assert load_metadata("test_meta.json") == {"РусскаяТаблица": ["ID:int"]}
        assert not Path("test_meta.json.tmp").exists()
    finally:
        os.chdir(original_directory)
    print("PASS: модули, отсутствие классов, допустимые импорты и JSON-функции")


def main():
    """Выполняет все сценарии и сохраняет общий проверяемый отчёт."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = StringIO()
    try:
        with redirect_stdout(report):
            check_persistence_and_crud()
            check_invalid_commands()
            check_corrupted_files()
            check_functions_and_cache()
            check_structure_and_io()
            output = session(
                "09-drop-and-recreate",
                [
                    "drop_table users",
                    "y",
                    "list_tables",
                    "create_table users name:str",
                    'insert into users values ("Fresh")',
                    "select from users",
                    "drop_table users",
                    "y",
                    "exit",
                ],
            )
            assert "Таблиц пока нет." in output
            assert '"users" успешно удалена.' in output
            assert not (WORKSPACE / "data/users.json").exists()
            assert json.loads((WORKSPACE / "db_meta.json").read_text()) == {}
            output = session("10-after-drop-and-eof", ["list_tables"])
            assert "Таблиц пока нет." in output
            assert "Выход из программы." in output
            print("PASS: drop удаляет схему и файл; повторное создание и EOF")
            print("ALL LOCAL SCENARIOS PASSED")
    finally:
        (LOG_DIR / "scenarios-summary.txt").write_text(
            report.getvalue(), encoding="utf-8"
        )
        print(report.getvalue(), end="")


if __name__ == "__main__":
    main()
