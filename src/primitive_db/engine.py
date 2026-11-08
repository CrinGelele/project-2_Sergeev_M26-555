#Этап 2

import shlex

import prompt

from primitive_db import core
from primitive_db.constants import COMMAND_PROMPT, META_FILE
from primitive_db.utils import load_metadata, save_metadata


def run():
    print("Команды: create_table, list_tables, drop_table, help, exit")
    while True:
        try:
            arguments = shlex.split(prompt.string(COMMAND_PROMPT, empty=True) or "")
            if not arguments:
                continue
            command, *values = arguments
            if command == "exit":
                break
            metadata = load_metadata(META_FILE)
            if command == "create_table" and len(values) >= 2:
                metadata = core.create_table(metadata, values[0], values[1:])
                save_metadata(META_FILE, metadata)
                print("Таблица создана.")
            elif command == "drop_table" and len(values) == 1:
                metadata = core.drop_table(metadata, values[0])
                save_metadata(META_FILE, metadata)
                print("Таблица удалена.")
            elif command == "list_tables" and not values:
                print("\n".join(core.list_tables(metadata)) or "Таблиц пока нет.")
            elif command == "help":
                print("create_table <имя> <поля>; list_tables; drop_table <имя>; exit")
            else:
                print("Неизвестная команда или неверные аргументы.")
        except (ValueError, KeyError, OSError) as error:
            print(f"Ошибка: {error}")
        except (EOFError, KeyboardInterrupt):
            break
