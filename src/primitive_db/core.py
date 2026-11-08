#Этап 2

from primitive_db.constants import ID_DEFINITION, VALID_TYPES
from primitive_db.utils import validate_name


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


def drop_table(metadata, table_name):
    """Удаляет схему таблицы после подтверждения, возвращая новый словарь."""
    get_schema(metadata, table_name)
    result = metadata.copy()
    del result[table_name]
    return result


def list_tables(metadata):
    """Возвращает отсортированный список имён таблиц."""
    return sorted(metadata)
