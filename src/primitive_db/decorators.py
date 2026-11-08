#Этап 3


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
