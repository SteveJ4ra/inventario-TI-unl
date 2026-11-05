"""Recorrido real de 006 en Chrome y PostgreSQL efímero, sin tocar la DB local.

Desde raíz (Playwright se instala solo en el entorno temporal de uv):
  PG_BIN=/usr/lib/postgresql/17/bin uv run --no-project --with playwright python backend/tools/smoke_license_lots.py

Requiere backend/.venv preparado, npm ci y Google Chrome instalado.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import secrets
import signal
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright
from test_postgres import BACKEND, postgres_environment

ROOT = BACKEND.parent
PYTHON = BACKEND / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(url, process):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Un servidor temporal terminó antes de estar listo.")
        try:
            with urlopen(url, timeout=1):
                return
        except HTTPError as exc:
            if exc.code < 500:
                return
        except (URLError, TimeoutError):
            pass
        time.sleep(0.1)
    raise RuntimeError("El servidor temporal no respondió en 30 segundos.")


def stop_owned(process):
    if process.poll() is None:
        if os.name == "nt":
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def main():
    chrome = Path(os.environ.get("LICENSE_SMOKE_CHROME", "/usr/bin/google-chrome"))
    if not chrome.is_file():
        raise SystemExit("Configura LICENSE_SMOKE_CHROME con un Chrome instalado.")
    with postgres_environment() as env, tempfile.TemporaryDirectory(
        prefix="license-browser-"
    ) as tmp:
        api_port, web_port = free_port(), free_port()
        while web_port == api_port:
            web_port = free_port()
        env.update(
            SMOKE006_PASSWORD=secrets.token_urlsafe(32),
            DJANGO_CSRF_TRUSTED_ORIGINS=f"http://127.0.0.1:{web_port}",
            VITE_PROXY_TARGET=f"http://127.0.0.1:{api_port}",
        )
        processes = []
        with (Path(tmp) / "servers.log").open("w+") as log:
            try:

                def run_manage(*args):
                    subprocess.run(
                        [str(PYTHON), str(BACKEND / "manage.py"), *args],
                        env=env,
                        cwd=ROOT,
                        check=True,
                        stdout=log,
                        stderr=log,
                    )

                run_manage("migrate", "--noinput")
                run_manage(
                    "shell",
                    "-c",
                    "import os; from django.contrib.auth import get_user_model; from django.contrib.auth.models import Group; g,_=Group.objects.get_or_create(name='Gestores'); [(u.groups.add(g)) for u in [get_user_model().objects.create_user(username=n,password=os.environ['SMOKE006_PASSWORD']) for n in ['smoke006','smoke006b']]]",
                )
                api = subprocess.Popen(
                    [
                        str(PYTHON),
                        str(BACKEND / "manage.py"),
                        "runserver",
                        f"127.0.0.1:{api_port}",
                        "--noreload",
                    ],
                    cwd=ROOT,
                    env=env,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
                processes.append(api)
                web = subprocess.Popen(
                    [
                        "node",
                        str(ROOT / "frontend/node_modules/vite/bin/vite.js"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(web_port),
                        "--strictPort",
                    ],
                    cwd=ROOT / "frontend",
                    env=env,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
                processes.append(web)
                base = f"http://127.0.0.1:{web_port}"
                wait_ready(f"http://127.0.0.1:{api_port}/api/auth/csrf/", api)
                wait_ready(base, web)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(
                        executable_path=str(chrome), headless=True
                    )
                    try:
                        first = browser.new_context(
                            viewport={"width": 1366, "height": 900}
                        )
                        second = browser.new_context()
                        page = first.new_page()
                        other = second.new_page()
                        errors = []
                        page.on("pageerror", lambda exc: errors.append(str(exc)))
                        other.on("pageerror", lambda exc: errors.append(str(exc)))

                        def login(target, name):
                            target.goto(base)
                            target.get_by_label("Usuario", exact=True).fill(name)
                            target.get_by_label("Contraseña", exact=True).fill(
                                env["SMOKE006_PASSWORD"]
                            )
                            target.get_by_role(
                                "button", name="Ingresar", exact=True
                            ).click()
                            target.get_by_role(
                                "button", name="Licencias", exact=False
                            ).click()
                            expect(
                                target.get_by_role(
                                    "heading", name="Lotes de licencias", exact=True
                                )
                            ).to_be_visible()

                        login(page, "smoke006")
                        page.get_by_role(
                            "button", name="＋ Registrar lote", exact=True
                        ).click()
                        page.get_by_label("Producto", exact=True).fill(
                            "Prueba navegador 006"
                        )
                        page.get_by_label("Proveedor", exact=True).fill(
                            "Proveedor ficticio"
                        )
                        page.get_by_label("Modalidad", exact=True).select_option(
                            "USER_SEAT"
                        )
                        page.get_by_label("Cantidad comprada", exact=True).fill("0")
                        page.get_by_label("Cantidad en uso", exact=True).fill("0")
                        page.get_by_label("Inicio de vigencia", exact=True).fill(
                            "2026-01-01"
                        )
                        page.get_by_role(
                            "button", name="Registrar lote", exact=True
                        ).click()
                        expect(
                            page.get_by_text("Remanentes: 0", exact=True)
                        ).to_be_visible()
                        page.get_by_role(
                            "button", name="Editar lote", exact=True
                        ).click()
                        page.get_by_label("Proveedor", exact=True).fill(
                            "Proveedor corregido"
                        )
                        page.get_by_label("Modalidad", exact=True).select_option(
                            "DEVICE_SEAT"
                        )
                        page.get_by_label("Cantidad comprada", exact=True).fill("10")
                        page.get_by_label("Cantidad en uso", exact=True).fill("4")
                        yesterday = (
                            datetime.now(timezone.utc).date() - timedelta(days=1)
                        ).isoformat()
                        page.get_by_label(
                            "Fin de vigencia · opcional", exact=True
                        ).fill(yesterday)
                        page.get_by_role(
                            "button", name="Guardar cambios", exact=True
                        ).click()
                        expect(
                            page.get_by_text("Remanentes: 6", exact=True)
                        ).to_be_visible()
                        expect(
                            page.get_by_text(
                                "Lote vencido: los remanentes no representan puestos utilizables.",
                                exact=True,
                            )
                        ).to_be_visible()
                        expect(
                            page.get_by_role("heading", name="Historial del lote")
                        ).to_be_visible()

                        page.get_by_role(
                            "button", name="Editar lote", exact=True
                        ).click()
                        login(other, "smoke006b")
                        other.get_by_role(
                            "button", name="Ver lote Prueba navegador 006", exact=True
                        ).click()
                        other.get_by_role(
                            "button", name="Editar lote", exact=True
                        ).click()
                        other.get_by_label("Cantidad en uso", exact=True).fill("2")
                        other.get_by_role(
                            "button", name="Guardar cambios", exact=True
                        ).click()
                        expect(
                            other.get_by_text("Remanentes: 8", exact=True)
                        ).to_be_visible()
                        page.get_by_label("Cantidad en uso", exact=True).fill("3")
                        page.get_by_role(
                            "button", name="Guardar cambios", exact=True
                        ).click()
                        expect(page.get_by_role("alert")).to_contain_text(
                            "No se reenviaron tus cambios"
                        )
                        expect(
                            page.get_by_text("Remanentes: 8", exact=True)
                        ).to_be_visible()
                        history = first.request.get(
                            base + "/api/license-lots/1/history/"
                        )
                        assert history.status == 200 and history.json()["count"] == 3
                        rejected = first.request.patch(
                            base + "/api/license-lots/1/",
                            data={"expected_revision": 2, "in_use_quantity": 1},
                        )
                        assert rejected.status == 403
                        page.set_viewport_size({"width": 375, "height": 812})
                        expect(
                            page.get_by_role("button", name="Licencias", exact=False)
                        ).to_be_visible()
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        )
                        page.screenshot(
                            path="/tmp/inventario006-mobile.png", full_page=True
                        )
                        page.get_by_role(
                            "button", name="Cerrar sesión", exact=False
                        ).click()
                        expect(
                            page.get_by_role("button", name="Ingresar", exact=True)
                        ).to_be_visible()
                        assert not errors, errors
                        print(
                            "PASS navegador real: login, alta cero/fin opcional, edición auditada, vencido/remanentes, dos gestores con conflicto 409, CSRF rechazado, móvil 375px y logout. PostgreSQL efímero; ninguna cuenta/dato en la DB local."
                        )
                    finally:
                        browser.close()
            except Exception:
                log.flush()
                log.seek(0)
                # Logs de datos ficticios; se redacta cualquier contraseña accidental.
                print(
                    log.read()
                    .replace(env["SMOKE006_PASSWORD"], "[redactado]")
                    .replace(env["DB_PASSWORD"], "[redactado]")
                )
                raise
            finally:
                for process in reversed(processes):
                    stop_owned(process)


if __name__ == "__main__":
    main()
