# Python, ДЗ №2 — примитивная база данных

Сергеев Максим Александрович, группа М26-555.

Консольная БД с таблицами, типами `int`, `str`, `bool` и JSON-хранилищем.
Схемы сохраняются в `db_meta.json`, записи — в `data/<таблица>.json`.

## Установка и запуск

Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
make install
make run
```

Без make: `uv sync --locked`, затем `uv run database`.
Для установки собранного пакета: `uv build`, затем `uv tool install dist/*.whl`.

## Управление таблицами

```text
create_table users name:str age:int is_active:bool
list_tables
info users
drop_table users
```

`ID:int` создаётся автоматически. Все поля обязательны.
`help` показывает справку, `exit` завершает работу.

## CRUD-операции

```text
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
delete from users where ID = 1
```

Строки задаются в кавычках, логические значения — `true`/`false`.
В `where` поддерживается одно равенство; в `set` можно перечислить несколько
присваиваний через запятую. `update` и `delete` требуют условия `where`.

## Декораторы и кэш

Ошибки перехватываются декоратором `handle_db_errors`. Удаление таблиц и строк
требует ответа `y`; любой другой ответ отменяет действие. `log_time` выводит
время выполнения `insert` и `select`. Замыкание `create_cacher` сохраняет
результаты выборок; после изменения записей старый результат не используется.

## Проверка и демонстрация

```bash
make lint
make test
make check
```

Исходники находятся в `src/primitive_db`: `core` — таблицы и CRUD,
`utils` — JSON, `parser` — команды, `engine` — консольный цикл,
`decorators` — обработка ошибок, подтверждение и кэш,
`constants` — настройки, `main` — точка входа.

[![Полный цикл работы базы данных](demo/database.gif)](https://asciinema.org/a/wAZ7c6q2iQWkoMuS)

[Открыть запись в asciinema](https://asciinema.org/a/wAZ7c6q2iQWkoMuS).
[Исходная запись](demo/database.cast) воспроизводится командой
`asciinema play demo/database.cast`. Новая запись: `make demo`.
