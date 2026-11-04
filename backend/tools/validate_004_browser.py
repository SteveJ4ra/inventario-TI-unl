"""Ejecuta el recorrido 004 en Chromium contra Django, Vite y PostgreSQL temporal."""

from contextlib import ExitStack, contextmanager
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from test_postgres import BACKEND, HIDDEN, postgres_environment

ROOT = BACKEND.parent
FRONTEND = ROOT / "frontend"
SCENARIO = ROOT / "specs/004-novedades-mantenimiento/checks/browser.cjs"
SEED = """
import os
from django.contrib.auth.models import Group, User
from inventory.services import create_asset, create_custodian

actor = User.objects.create_user("gestor-004", password=os.environ["VALIDATION_004_LOGIN"])
actor.groups.add(Group.objects.create(name="Gestores"))
create_custodian(actor=actor, data={
    "full_name": "Custodia ficticia 004", "email": "custodia004@example.org",
})
create_asset(actor=actor, data={
    "name": "Activo ficticio 004", "description": "Validación integral 004",
    "category": "portatil", "brand": "Prueba", "model": "004",
    "serial_number": "SMOKE-004", "location": "Laboratorio", "condition": "operativo",
})
"""


def free_ports():
    with socket.socket() as backend, socket.socket() as frontend:
        for listener in (backend, frontend):
            listener.bind(("127.0.0.1", 0))
        return backend.getsockname()[1], frontend.getsockname()[1]


@contextmanager
def server(command, cwd, env):
    process = subprocess.Popen(
        command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=HIDDEN,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def wait_for_server(process, url):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"El servidor terminó antes de responder: {url}")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"El servidor no respondió: {url}")


def main():
    node = shutil.which("node")
    vite = FRONTEND / "node_modules/vite/bin/vite.js"
    for variable in ("VALIDATION_004_PLAYWRIGHT", "VALIDATION_004_CHROMIUM"):
        if not Path(os.environ.get(variable, "")).exists() or not os.environ.get(variable):
            raise RuntimeError(f"Configura {variable} con una ruta existente.")
    if not node or not vite.is_file():
        raise RuntimeError("Se necesita Node.js y npm ci en frontend.")

    with postgres_environment() as env, ExitStack() as stack:
        backend_port, frontend_port = free_ports()
        origin = f"http://127.0.0.1:{frontend_port}"
        backend_url = f"http://127.0.0.1:{backend_port}"
        env.update(
            VALIDATION_004_URL=origin,
            VALIDATION_004_LOGIN=secrets.token_urlsafe(30),
            DJANGO_CSRF_TRUSTED_ORIGINS=origin,
            VITE_PROXY_TARGET=backend_url,
        )
        manage = [sys.executable, str(BACKEND / "manage.py")]
        subprocess.run([*manage, "migrate", "--noinput"], cwd=BACKEND, env=env, check=True)
        subprocess.run([*manage, "shell", "-c", SEED], cwd=BACKEND, env=env, check=True)
        django = stack.enter_context(server(
            [*manage, "runserver", f"127.0.0.1:{backend_port}", "--noreload"],
            BACKEND, env,
        ))
        wait_for_server(django, f"{backend_url}/api/auth/csrf/")
        web = stack.enter_context(server(
            [node, str(vite), "--host", "127.0.0.1", "--port", str(frontend_port), "--strictPort"],
            FRONTEND, env,
        ))
        wait_for_server(web, origin)
        subprocess.run([node, str(SCENARIO)], cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()
