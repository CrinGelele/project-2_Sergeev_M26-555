"""Чтение и сохранение метаданных и строк в JSON-файлах."""

#Этап 3

import json
import os

from primitive_db.constants import DATA_DIR, ENCODING, JSON_INDENT


def validate_name(name):
    """Разрешает идентификаторы, исключая пути к посторонним файлам."""
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError(f"Некорректное значение: {name}. Попробуйте снова.")


def load_metadata(filepath):
    """Загружает словарь метаданных или возвращает {} для новой базы."""
    try:
        with open(filepath, encoding=ENCODING) as file:
            metadata = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("Метаданные должны быть JSON-объектом.")
    return metadata


def save_json(filepath, data):
    """Сначала записывает временный файл, затем заменяет основной."""
    temporary_path = filepath + ".tmp"
    try:
        with open(temporary_path, "w", encoding=ENCODING) as file:
            json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
            file.write("\n")
        os.replace(temporary_path, filepath)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def save_metadata(filepath, data):
    """Сохраняет переданный словарь метаданных."""
    save_json(filepath, data)


def table_filepath(table_name):
    """Строит путь к файлу таблицы после проверки её имени."""
    validate_name(table_name)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загружает список строк или возвращает [] при отсутствии файла."""
    try:
        with open(table_filepath(table_name), encoding=ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        raise ValueError("Данные таблицы должны быть JSON-массивом.")
    return data


def save_table_data(table_name, data):
    """Создаёт каталог data и сохраняет строки таблицы."""
    filepath = table_filepath(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    save_json(filepath, data)


def remove_table_data(table_name):
    """Удаляет файл таблицы, если он существует."""
    filepath = table_filepath(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)
