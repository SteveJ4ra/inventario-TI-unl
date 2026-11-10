"""Ejecuta las pruebas Django en PostgreSQL efímero, sin tocar el .env local."""

from contextlib import contextmanager
from pathlib import Path
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile

BACKEND = Path(__file__).resolve().parents[1]
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


@contextmanager
def postgres_environment():
    configured = os.environ.get("PG_BIN")
    bindir = (
        Path(configured) if configured else Path(r"C:/Program Files/PostgreSQL/17/bin")
    )

    def executable(name):
        candidate = bindir / (name + (".exe" if os.name == "nt" else ""))
        found = str(candidate) if candidate.is_file() else shutil.which(name)
        if not found:
            raise RuntimeError(
                "No se encontró "
                + name
                + ". Configura PG_BIN con la carpeta bin de PostgreSQL."
            )
        return found

    initdb, pgctl = executable("initdb"), executable("pg_ctl")
    temp_parent = Path(tempfile.gettempdir()).resolve()
    directory = Path(
        tempfile.mkdtemp(prefix="inventario-tests-", dir=temp_parent)
    ).resolve()
    assert directory.parent == temp_parent and directory.name.startswith(
        "inventario-tests-"
    )
    data = directory / "data"
    password = secrets.token_urlsafe(32)
    pwfile = directory / "password"
    pwfile.write_text(password, encoding="utf-8")
    pwfile.chmod(0o600)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    def run(args):
        # Un archivo evita esperar EOF de handles heredados por postgres en Windows.
        with (directory / "launcher.log").open("w", encoding="utf-8") as output:
            result = subprocess.run(
                args,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=HIDDEN,
            )
        if result.returncode:
            logs = [directory / "launcher.log", directory / "postgres.log"]
            detail = "\n".join(
                log.read_text(encoding="utf-8", errors="replace")
                for log in logs
                if log.exists()
            )
            raise RuntimeError(detail.replace(password, "[redactado]"))

    try:
        run(
            [
                initdb,
                "-D",
                str(data),
                "-U",
                "inventory_test",
                "--pwfile=" + str(pwfile),
                "--auth=scram-sha-256",
                "--encoding=UTF8",
                "--locale=C",
                "--locale-provider=icu",
                "--icu-locale=und",
            ]
        )
        server_options = f"-h 127.0.0.1 -p {port}"
        if os.name != "nt":
            # El usuario normal no puede escribir sockets en /var/run/postgresql.
            # Usamos su directorio temporal privado, nunca el clúster del sistema.
            server_options += f' -k "{directory}"'
        run(
            [
                pgctl,
                "-D",
                str(data),
                "-l",
                str(directory / "postgres.log"),
                "-o",
                server_options,
                "-w",
                "start",
            ]
        )
        env = os.environ.copy()
        env.update(
            DB_NAME="postgres",
            DB_USER="inventory_test",
            DB_PASSWORD=password,
            DB_HOST="127.0.0.1",
            DB_PORT=str(port),
            DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
            DJANGO_DEBUG="False",
            PYTHONDONTWRITEBYTECODE="1",
        )
        yield env
    finally:
        if (data / "postmaster.pid").exists():
            run([pgctl, "-D", str(data), "-m", "fast", "-w", "stop"])
        # Solo se elimina el directorio nuevo creado por esta invocación.
        if directory.resolve().parent != temp_parent or not directory.name.startswith(
            "inventario-tests-"
        ):
            raise RuntimeError("Ruta temporal fuera de la carpeta autorizada")
        shutil.rmtree(directory)


def main():
    with postgres_environment() as env:
        args = sys.argv[1:]
        if args[:1] == ["--manage"]:
            command = args[1:]
            if not (command == ["check"] or command == ["makemigrations", "--check", "--dry-run"]):
                raise ValueError("--manage admite solo check o makemigrations --check --dry-run.")
        else:
            command = ["test", *(args or ["inventory", "--verbosity", "2"])]
        result = subprocess.run(
            [sys.executable, str(BACKEND / "manage.py"), *command],
            cwd=BACKEND,
            env=env,
        )
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
