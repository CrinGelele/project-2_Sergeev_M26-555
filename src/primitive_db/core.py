"""Управление схемами, валидация и CRUD без классов."""

#Этап 4

import json

from primitive_db.constants import ID_COLUMN, ID_DEFINITION, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, validate_name

cache_select = create_cacher()


def get_schema(metadata, table_name):
    """Проверяет таблицу и возвращает упорядоченный словарь её типов."""
    validate_name(table_name)
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')
    columns = metadata[table_name]
    if not isinstance(columns, list) or not columns or columns[0] != ID_DEFINITION:
        raise ValueError(
            "Некорректная схема таблицы: первый столбец должен быть ID:int."
        )
    schema = {}
    for column in columns:
        if not isinstance(column, str) or column.count(":") != 1:
            raise ValueError(f"Некорректное описание столбца: {column}.")
        name, data_type = column.split(":")
        validate_name(name)
        if name in schema or data_type not in VALID_TYPES:
            raise ValueError(f"Повторный столбец или неизвестный тип: {column}.")
        schema[name] = data_type
    return schema


def validate_clause(schema, clause, updating=False):
    """Проверяет существование полей и точное соответствие Python-типов."""
    if not clause:
        raise ValueError("Условие или список изменений не может быть пустым.")
    for column, value in clause.items():
        if column not in schema:
            raise KeyError(column)
        if updating and column == ID_COLUMN:
            raise ValueError("Автоматический ID изменять нельзя.")
        if type(value) is not VALID_TYPES[schema[column]]:
            raise ValueError(f"Для столбца {column} требуется тип {schema[column]}.")


def validate_rows(schema, rows):
    """Отклоняет повреждённые строки и повторяющиеся ID до изменения данных."""
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict) or row.keys() != schema.keys():
            raise ValueError("Состав полей записи не соответствует схеме таблицы.")
        validate_clause(schema, row)
        if row[ID_COLUMN] < 1 or row[ID_COLUMN] in identifiers:
            raise ValueError("ID должен быть положительным и уникальным.")
        identifiers.add(row[ID_COLUMN])


def matches(row, where_clause):
    """Сравнивает значения вместе с типами, различая True и 1."""
    return all(
        column in row and type(row[column]) is type(value) and row[column] == value
        for column, value in where_clause.items()
    )


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт схему с автоматическим ID, не меняя исходный словарь."""
    validate_name(table_name)
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not columns:
        raise ValueError("Укажите хотя бы один столбец.")
    result = metadata.copy()
    result[table_name] = [ID_DEFINITION, *columns]
    get_schema(result, table_name)
    return result


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет схему таблицы после подтверждения, возвращая новый словарь."""
    get_schema(metadata, table_name)
    result = metadata.copy()
    del result[table_name]
    return result


@handle_db_errors
def list_tables(metadata):
    """Возвращает отсортированный список имён таблиц."""
    return sorted(metadata)


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Проверяет значения и добавляет запись с max(ID) + 1."""
    schema = get_schema(metadata, table_name)
    columns = list(schema)[1:]
    if len(values) != len(columns):
        raise ValueError(f"Ожидается {len(columns)} значений без ID.")
    row = dict(zip(columns, values, strict=True))
    validate_clause(schema, row)
    data = load_table_data(table_name)
    validate_rows(schema, data)
    row = {ID_COLUMN: max((item[ID_COLUMN] for item in data), default=0) + 1, **row}
    return [*data, row]


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Кэширует запрос по снимку данных; возвращает независимые копии строк."""
    key = json.dumps([table_data, where_clause], sort_keys=True, ensure_ascii=False)

    def calculate():
        """Вычисляет выборку при первом запросе к этому снимку данных."""
        return [
            row.copy()
            for row in table_data
            if (where_clause is None or matches(row, where_clause))
        ]

    return [row.copy() for row in cache_select(key, calculate)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет совпавшие записи, оставляя исходные данные без изменений."""
    if not set_clause or not where_clause:
        raise ValueError("Для update нужны set и where.")
    if ID_COLUMN in set_clause:
        raise ValueError("Автоматический ID изменять нельзя.")
    for row in table_data:
        for column, value in set_clause.items():
            if column not in row:
                raise KeyError(column)
            if type(value) is not type(row[column]):
                raise ValueError(f"Неверный тип значения столбца {column}.")
    return [
        {**row, **set_clause} if matches(row, where_clause) else row.copy()
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет совпавшие строки после подтверждения пользователя."""
    if not where_clause:
        raise ValueError("Для delete требуется условие where.")
    return [row.copy() for row in table_data if not matches(row, where_clause)]
