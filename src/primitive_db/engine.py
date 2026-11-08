"""Консольный цикл, вызов команд, сохранение и табличный вывод."""

#Этап 3

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import COMMAND_PROMPT, HELP_TEXT, ID_COLUMN, META_FILE
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Prints the help message for the current mode."""
    print(HELP_TEXT)


def print_rows(schema, rows):
    """Печатает строки с заголовками, в том числе для пустой выборки."""
    table = PrettyTable()
    table.field_names = list(schema)
    for row in rows:
        table.add_row([row[column] for column in schema])
    print(table)


@handle_db_errors
def execute_command(user_input):
    """Выполняет одну команду; True означает запрос на выход."""
    arguments = parse_command(user_input)
    command = arguments["command"]
    if command == "exit":
        return True
    if command == "help":
        print_help()
        return False
    if not command:
        return False
    if command not in {
        "create_table",
        "drop_table",
        "list_tables",
        "insert",
        "select",
        "update",
        "delete",
        "info",
    }:
        print(f"Функции {command} нет. Попробуйте снова.")
        return False
    metadata = load_metadata(META_FILE)
    if command == "list_tables":
        names = core.list_tables(metadata)
        if names is not None:
            print("\n".join(f"- {name}" for name in names) or "Таблиц пока нет.")
        return False
    table_name = arguments["table"]
    if command == "create_table":
        result = core.create_table(metadata, table_name, arguments["columns"])
        if result is not None:
            save_table_data(table_name, [])
            save_metadata(META_FILE, result)
            columns = ", ".join(result[table_name])
            print(f'Таблица "{table_name}" успешно создана со столбцами: {columns}')
        return False
    schema = core.get_schema(metadata, table_name)
    if command == "drop_table":
        result = core.drop_table(metadata, table_name)
        if result is not None:
            remove_table_data(table_name)
            save_metadata(META_FILE, result)
            print(f'Таблица "{table_name}" успешно удалена.')
        return False
    data = load_table_data(table_name)
    core.validate_rows(schema, data)
    if command == "info":
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {', '.join(metadata[table_name])}")
        print(f"Количество записей: {len(data)}")
        return False
    if arguments.get("where") is not None:
        core.validate_clause(schema, arguments["where"])
    if command == "select":
        result = core.select(data, arguments["where"])
        if result is not None:
            print_rows(schema, result)
    elif command == "insert":
        result = core.insert(metadata, table_name, arguments["values"])
        if result is not None:
            save_table_data(table_name, result)
            identifier = result[-1][ID_COLUMN]
            print(
                f'Запись с ID={identifier} успешно добавлена в таблицу "{table_name}".'
            )
    elif command == "update":
        core.validate_clause(schema, arguments["set"], updating=True)
        result = core.update(data, arguments["set"], arguments["where"])
        if result is not None:
            save_table_data(table_name, result)
            updated_ids = [
                row[ID_COLUMN] for row in data if core.matches(row, arguments["where"])
            ]
            for identifier in updated_ids:
                print(
                    f'Запись с ID={identifier} в таблице "{table_name}" '
                    "успешно обновлена."
                )
            if not updated_ids:
                print("Подходящих записей нет.")
    elif command == "delete":
        result = core.delete(data, arguments["where"])
        if result is not None:
            save_table_data(table_name, result)
            deleted_ids = [
                row[ID_COLUMN] for row in data if core.matches(row, arguments["where"])
            ]
            for identifier in deleted_ids:
                print(
                    f"Запись с ID={identifier} успешно удалена "
                    f'из таблицы "{table_name}".'
                )
            if not deleted_ids:
                print("Подходящих записей нет.")
    return False


def run():
    """Запускает БД и завершает её по exit, EOF или Ctrl+C."""
    print_help()
    while True:
        try:
            user_input = prompt.string(COMMAND_PROMPT, empty=True) or ""
            if execute_command(user_input) is True:
                break
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break
