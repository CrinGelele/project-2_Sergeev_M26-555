# Python, ДЗ №2

Сергеев Максим Александрович, группа М26-555.

Консольная база данных: таблицы, CRUD, типы `int`, `str`, `bool`, хранение в JSON.
Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
make install
make run
```

## Управление таблицами

`ID:int` добавляется автоматически. `help` — справка, `exit` — выход.

```text
create_table users name:str age:int
list_tables
info users
drop_table users
```

## CRUD-операции

```text
insert into users values ("Maxim", 25)
select from users
select from users where age = 25
update users set age = 26 where ID = 1
delete from users where ID = 1
```

Ошибки выводятся сообщением; удаление требует `y`, другой ответ отменяет действие.
Замеряется время `insert`/`select`; результаты выборок кэшируются.

[![Демонстрация](https://asciinema.org/a/M5f3zEX3oQcqvZFF.svg)](https://asciinema.org/a/M5f3zEX3oQcqvZFF)

[GIF](demo/database.gif) · [Запись](demo/database.cast)
