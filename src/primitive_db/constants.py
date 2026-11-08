"""Настройки файлов, типов и команд базы данных."""

#Этап 2

META_FILE = "db_meta.json"
DATA_DIR = "data"
ENCODING = "utf-8"
JSON_INDENT = 2
ID_COLUMN = "ID"
ID_DEFINITION = "ID:int"
VALID_TYPES = {"int": int, "str": str, "bool": bool}
BOOLEAN_VALUES = {"true": True, "false": False}
MAX_CACHE_ENTRIES = 100
COMMAND_PROMPT = ">>>Введите команду: "
HELP_TEXT = """
***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу

***Операции с данными***
<command> insert into <имя_таблицы> values (<значение1>, ...) - создать запись
<command> select from <имя_таблицы> [where <столбец> = <значение>] - прочитать
<command> update <имя_таблицы> set <столбец> = <значение> where <столбец> = <значение>
<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить записи
<command> info <имя_таблицы> - информация о таблице

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация
Типы: int, str, bool. Строки в кавычках, bool: true или false.
"""
