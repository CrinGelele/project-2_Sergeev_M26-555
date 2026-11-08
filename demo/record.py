"""Записывает настоящий PTY-сеанс в локальный asciicast v2 без публикации."""

#Этап 5

import fcntl
import html
import json
import os
import pty
import select
import shutil
import struct
import subprocess
import termios
import time
from pathlib import Path

from primitive_db.constants import COMMAND_PROMPT

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "demo"
WORKSPACE = ROOT / ".demo-workspaces" / str(time.time_ns())


def main():
    """Запускает оболочку, устанавливает пакет и показывает весь цикл CRUD."""
    DEMO_DIR.mkdir(exist_ok=True)
    WORKSPACE.parent.mkdir(exist_ok=True)
    shutil.copytree(
        ROOT,
        WORKSPACE,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".local",
            "dist",
            "data",
            ".demo-workspaces",
            ".test-output",
            "__pycache__",
        ),
    )
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
    environment = {**os.environ, "PS1": "demo$ ", "TERM": "dumb", "NO_COLOR": "1"}

    def set_controlling_terminal():
        """Подключает PTY как управляющий терминал дочерней оболочки."""
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = subprocess.Popen(
        ["/bin/sh", "--noediting", "-i"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=WORKSPACE,
        env=environment,
        start_new_session=True,
        preexec_fn=set_controlling_terminal,
    )
    os.close(slave)
    started = time.monotonic()
    header = {
        "version": 2,
        "width": 120,
        "height": 40,
        "timestamp": int(time.time()),
        "title": "primitive_db: установка и полный CRUD",
        "env": {"TERM": "dumb", "SHELL": "/bin/sh"},
    }
    events = []

    def receive(expected):
        """Читает фактический вывод до приглашения, сохраняя время каждого блока."""
        received = b""
        deadline = time.monotonic() + 90
        while expected.encode() not in received:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Не появилось приглашение {expected!r}: {received!r}"
                )
            ready, _, _ = select.select([master], [], [], 1)
            if ready:
                chunk = os.read(master, 65536)
                if not chunk:
                    raise RuntimeError("Сеанс завершился до ожидаемого приглашения.")
                received += chunk
                events.append([time.monotonic() - started, "o", chunk.decode("utf-8")])

    def send(command, next_prompt):
        """Передаёт команду терминалу; её отображает настоящий терминальный echo."""
        time.sleep(0.25)
        os.write(master, (command + "\n").encode())
        receive(next_prompt)

    try:
        receive("demo$ ")
        send("make install", "demo$ ")
        send("uv run database", COMMAND_PROMPT)
        for command in [
            "create_table users name:str age:int is_active:bool",
            "list_tables",
            'insert into users values ("Sergei", 28, true)',
            'insert into users values ("Anna, where = set", 20, false)',
            "select from users",
            'select from users where name = "Sergei"',
            'update users set age = 29 where name = "Sergei"',
            "select from users where age = 29",
            'insert into users values ("Wrong", "age", true)',
        ]:
            send(command, COMMAND_PROMPT)
        send("delete from users where ID = 1", "[y/n]: ")
        send("n", COMMAND_PROMPT)
        send("select from users", COMMAND_PROMPT)
        send("delete from users where ID = 1", "[y/n]: ")
        send("y", COMMAND_PROMPT)
        send("select from users", COMMAND_PROMPT)
        send("info users", COMMAND_PROMPT)
        send("drop_table users", "[y/n]: ")
        send("y", COMMAND_PROMPT)
        send("list_tables", COMMAND_PROMPT)
        send("exit", "demo$ ")
        os.write(master, b"exit\n")
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        os.close(master)
    transcript = "".join(event[2] for event in events)
    assert "Ошибка валидации" in transcript
    assert "Операция отменена." in transcript
    assert "успешно обновлена" in transcript and "успешно удалена" in transcript
    assert not (WORKSPACE / "data/users.json").exists()
    assert json.loads((WORKSPACE / "db_meta.json").read_text()) == {}
    with (DEMO_DIR / "database.cast").open("w", encoding="utf-8") as file:
        for record in [header, *events]:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    (DEMO_DIR / "transcript.txt").write_text(transcript, encoding="utf-8")
    write_viewer(events, transcript)
    print(f"Создан настоящий локальный PTY-сеанс: {len(events)} блоков вывода.")
    print("Файлы: demo/database.cast, demo/transcript.txt, demo/index.html")


def write_viewer(events, transcript):
    """Создаёт автономный просмотр записи с управлением воспроизведением."""
    encoded_events = json.dumps(events, ensure_ascii=False).replace("<", "\\u003c")
    document = """<!doctype html>
<html lang="ru"><meta charset="utf-8"><title>Демонстрация primitive_db</title>
<style>
body{margin:2rem;background:#111827;color:#e5e7eb;font:16px system-ui}
button{padding:.5rem 1rem;margin-right:.5rem;cursor:pointer}
pre{background:#030712;padding:1rem;overflow:auto;font:14px monospace;line-height:1.5}
</style>
<h1>primitive_db — локальная демонстрация</h1>
<p>Записанный вывод настоящего терминала. Установка, CRUD, отмена и подтверждение.
Времена записи сохранены в <a href="database.cast">asciicast v2</a>.</p>
<button id="play">Воспроизвести</button><button id="all">Показать всё</button>
<label>Скорость <select id="speed"><option value="1">1×</option>
<option value="0.2">0.2×</option></select></label>
<pre id="terminal">TRANSCRIPT</pre>
<script>
const events=EVENTS, screen=document.getElementById('terminal'); let timer;
document.getElementById('all').onclick=()=>{
 clearTimeout(timer);screen.textContent=events.map(e=>e[2]).join('');
};
document.getElementById('play').onclick=()=>{
 clearTimeout(timer);screen.textContent='';let i=0;
 const speed=Number(document.getElementById('speed').value);
 function next(){if(i>=events.length)return;screen.textContent+=events[i][2];i++;
  if(i<events.length)timer=setTimeout(next,1000*(events[i][0]-events[i-1][0])/speed);}
 next();
};
</script></html>"""
    document = document.replace("TRANSCRIPT", html.escape(transcript))
    document = document.replace("EVENTS", encoded_events)
    (DEMO_DIR / "index.html").write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
