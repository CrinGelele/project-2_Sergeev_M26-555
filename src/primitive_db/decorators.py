"""Обработка ошибок, подтверждение, замер времени и кэш-замыкание."""

#Этап 4

import time

import prompt

from primitive_db.constants import MAX_CACHE_ENTRIES


def preserve_name(wrapper, function):
    """Сохраняет имя и описание без дополнительных библиотек."""
    wrapper.__name__ = function.__name__
    wrapper.__doc__ = function.__doc__
    return wrapper


def handle_db_errors(function):
    """Выводит ошибку, возвращая None вместо успешного результата."""

    def wrapper(*args, **kwargs):
        """Перехватывает ошибки операции с базой данных."""
        try:
            return function(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, БД не инициализирована.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлами: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return preserve_name(wrapper, function)


def confirm_action(action_name):
    """Создаёт декоратор, отменяющий действие без ответа y."""

    def decorator(function):
        """Оборачивает выбранную опасную операцию."""

        def wrapper(*args, **kwargs):
            """Запрашивает подтверждение перед вызовом функции."""
            answer = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ',
                empty=True,
            )
            if (answer or "").strip().lower() != "y":
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return preserve_name(wrapper, function)

    return decorator


def log_time(function):
    """Измеряет длительность успешного вызова монотонными часами."""

    def wrapper(*args, **kwargs):
        """Запускает функцию и печатает фактическое время выполнения."""
        started = time.monotonic()
        result = function(*args, **kwargs)
        elapsed = time.monotonic() - started
        print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд")
        return result

    return preserve_name(wrapper, function)


def create_cacher():
    """Возвращает функцию с собственным ограниченным словарём-кэшем."""
    cache = {}

    def cache_result(key, value_func):
        """Вычисляет значение только при отсутствии ключа в кэше."""
        if key not in cache:
            value = value_func()
            if len(cache) >= MAX_CACHE_ENTRIES:
                cache.clear()
            cache[key] = value
        return cache[key]

    return cache_result
