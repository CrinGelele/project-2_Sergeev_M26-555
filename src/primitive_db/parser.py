"""Разбор команд, строковых литералов, values, where и set."""

#Этап 3

import shlex

from primitive_db.constants import BOOLEAN_VALUES


def tokenize(text):
    """Сохраняет кавычки; пунктуацию вне строк выделяет в токены."""
    tokens = []
    position = 0
    while position < len(text):
        character = text[position]
        if character.isspace():
            position += 1
        elif character in "(),=":
            tokens.append(character)
            position += 1
        elif character in "\"'":
            end = position + 1
            while end < len(text):
                if text[end] == "\\" and character == '"':
                    end += 2
                elif text[end] == character:
                    break
                else:
                    end += 1
            if end >= len(text):
                raise ValueError("Не закрыты кавычки.")
            literal = text[position : end + 1]
            shlex.split(literal)
            tokens.append(literal)
            position = end + 1
        else:
            end = position
            while end < len(text) and not text[end].isspace():
                if text[end] in "(),=\"'":
                    break
                end += 1
            tokens.extend(shlex.split(text[position:end]))
            position = end
    return tokens


def parse_value(token):
    """Разбирает int, true/false или строку в одинарных/двойных кавычках."""
    if token.startswith(("'", '"')):
        return shlex.split(token)[0]
    if token.lower() in BOOLEAN_VALUES:
        return BOOLEAN_VALUES[token.lower()]
    if token.lstrip("+-").isascii() and token.lstrip("+-").isdigit():
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки нужны в кавычках.")


def parse_values(text):
    """Разбирает обязательные значения в скобках, разделённые запятыми."""
    tokens = tokenize(text)
    if len(tokens) < 3 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Используйте values (<значение1>, <значение2>, ...).")
    items = tokens[1:-1]
    if len(items) % 2 == 0 or any(token != "," for token in items[1::2]):
        raise ValueError("Значения должны разделяться запятыми.")
    return [parse_value(token) for token in items[::2]]


def parse_assignments(text, multiple=False):
    """Превращает равенства column=value в словарь, сохраняя тип значения."""
    tokens = tokenize(text)
    if not tokens or (len(tokens) + 1) % 4:
        raise ValueError("Ожидается <столбец> = <значение>.")
    result = {}
    for start in range(0, len(tokens), 4):
        column, operator, value = tokens[start : start + 3]
        if operator != "=" or (start and tokens[start - 1] != ","):
            raise ValueError("Используйте равенство и запятые между полями set.")
        if column in result:
            raise ValueError(f"Столбец {column} указан дважды.")
        result[column] = parse_value(value)
    if not multiple and len(result) != 1:
        raise ValueError("В where поддерживается одно равенство.")
    return result


def parse_where(text):
    """Разбирает одно условие where с оператором равенства."""
    return parse_assignments(text)


def parse_set(text):
    """Разбирает одно или несколько присваиваний set через запятую."""
    return parse_assignments(text, multiple=True)


def require(condition, syntax):
    """Сообщает ожидаемый синтаксис при неверной структуре команды."""
    if not condition:
        raise ValueError(f"Используйте: {syntax}")


def parse_command(text):
    """Возвращает команду и аргументы; неверный синтаксис вызывает ValueError."""
    tokens = tokenize(text)
    if not tokens:
        return {"command": ""}
    command = tokens[0]
    result = {"command": command}
    if command in {"help", "exit", "list_tables"}:
        require(len(tokens) == 1, command)
    elif command == "create_table":
        require(len(tokens) >= 3, "create_table <таблица> <столбец:тип> ...")
        result.update(table=tokens[1], columns=tokens[2:])
    elif command in {"drop_table", "info"}:
        require(len(tokens) == 2, f"{command} <таблица>")
        result["table"] = tokens[1]
    elif command == "insert":
        require(
            len(tokens) >= 7 and tokens[1] == "into" and tokens[3] == "values",
            "insert into <таблица> values (<значения>)",
        )
        result.update(table=tokens[2], values=parse_values(" ".join(tokens[4:])))
    elif command in {"select", "delete"}:
        require(len(tokens) >= 3 and tokens[1] == "from", f"{command} from <таблица>")
        result.update(table=tokens[2], where=None)
        if len(tokens) > 3:
            require(tokens[3] == "where", f"{command} from <таблица> where <условие>")
            result["where"] = parse_where(" ".join(tokens[4:]))
        elif command == "delete":
            raise ValueError("Для delete требуется условие where.")
    elif command == "update":
        require(
            len(tokens) >= 10 and tokens[2] == "set",
            "update <таблица> set ... where ...",
        )
        where_positions = [
            index for index in range(6, len(tokens), 4) if tokens[index] == "where"
        ]
        require(len(where_positions) == 1, "update <таблица> set ... where ...")
        where_position = where_positions[0]
        result.update(
            table=tokens[1],
            set=parse_set(" ".join(tokens[3:where_position])),
            where=parse_where(" ".join(tokens[where_position + 1 :])),
        )
    return result
