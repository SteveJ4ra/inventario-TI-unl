"""Recorrido HTTP con datos ficticios en la base de demostración local. Sin claves impresas."""
import os
import json
import secrets
import uuid
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError

if os.environ.get("INVENTORY_ALLOW_DEMO_DATA") != "1":
    raise SystemExit("Esta prueba crea datos ficticios. Confirmar con INVENTORY_ALLOW_DEMO_DATA=1.")
if (os.environ.get("DB_HOST"), os.environ.get("DB_NAME"), os.environ.get("DB_USER")) != ("db", "inventario_ti", "inventario_app"):
    raise SystemExit("Solo se admite el servicio db/base de demostración previsto por Compose.")
import django
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.utils import timezone
from inventory.models import AcquisitionDocument, Faculty
from django.db import connection

run = uuid.uuid4().hex[:10]
password = secrets.token_urlsafe(40)
actor = get_user_model().objects.create_user("demo-s5-" + run, password=password)
actor.groups.add(Group.objects.get_or_create(name="Gestores")[0])
faculty = Faculty.objects.create(name="Demostración S5 " + run)
doc = AcquisitionDocument.objects.create(source="PURCHASE", reference="DEMO-S5-" + run,
    document_date=date(2026, 11, 6), supplier="Proveedor ficticio S5", invoice_total=Decimal("1000.00"), created_by=actor)
jar = CookieJar()
client = build_opener(HTTPCookieProcessor(jar))
results = []
base = "http://127.0.0.1:8000"


def call(path, payload=None, csrf=None, expected=200):
    headers = {"Accept": "application/json"}
    if csrf: headers["X-CSRFToken"] = csrf
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    request = Request(base + path, data=data, headers=headers)
    try:
        response = client.open(request, timeout=15)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read()
        status = response.status
        assert status == expected, (path, status, expected, body[:150])
        results.append({"endpoint": path, "estado": status})
        if path.startswith("/api/"):
            assert "no-store" in response.headers.get("Cache-Control", "")
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(body), response.headers
        return body, response.headers


try:
    call("/api/docs/")
    call("/api/openapi.json")
    call("/api/docs/live.js")
    call("/static/admin/css/base.css")
    call("/api/v1/assets/", expected=403)
    data, _ = call("/api/v1/auth/csrf/")
    call("/api/v1/auth/login/", {"username": actor.username, "password": password}, data["data"]["csrfToken"])
    session_id = next(c.value for c in jar if c.name == "sessionid")
    expiry = Session.objects.get(session_key=session_id).get_decoded()["_session_expiry"]
    remaining = (datetime.fromisoformat(expiry) - timezone.now()).total_seconds()
    assert 1780 < remaining <= 1800
    data, _ = call("/api/v1/auth/csrf/")
    csrf = data["data"]["csrfToken"]
    data, _ = call("/api/v1/custodians/", {"full_name": "Custodio ficticio S5", "email": run + "@example.org"}, csrf, 201)
    person = data["data"]
    payload = {"name": "Portátil demo S5", "description": "Datos ficticios de despliegue", "category": "portatil",
        "brand": "Demo", "model": "S5", "serial_number": run, "location": "Almacén demo", "condition": "operativo",
        "faculty_id": faculty.pk, "acquisition_document_id": doc.pk, "item_value": "300.00", "acquired_on": "2026-11-06"}
    call("/api/v1/assets/", {**payload, "name": ""}, csrf, 400)
    data, _ = call("/api/v1/assets/", payload, csrf, 201)
    asset = data["data"]
    call("/api/v1/assets/" + str(asset["id"]) + "/")
    path = "/api/v1/assets/" + str(asset["id"])
    call(path + "/return/", {"expected_revision": asset["revision"], "condition": "operativo", "reception_location": "Almacén demo"}, csrf, 409)
    data, _ = call(path + "/deliver/", {"expected_revision": asset["revision"], "custodian_id": person["id"], "destination": "Aula demo"}, csrf, 201)
    current = data["data"]["asset"]
    data, _ = call(path + "/return/", {"expected_revision": current["revision"], "condition": "operativo", "reception_location": "Almacén demo"}, csrf, 201)
    assert data["data"]["asset"]["assignment"] == "disponible"
    assert data["data"]["asset"]["current_custodian"] is None
    data, _ = call(path + "/movements/")
    assert len(data["data"]) == 2
    call("/api/assets/" + str(asset["id"]) + "/qr.svg")
    Session.objects.filter(session_key=session_id).update(expire_date=timezone.now())
    call("/api/v1/assets/", expected=403)
    for _ in range(5):
        data, _ = call("/api/v1/auth/csrf/")
        call("/api/v1/auth/login/", {"username": actor.username, "password": "incorrecta"}, data["data"]["csrfToken"], 400)
    data, _ = call("/api/v1/auth/csrf/")
    _, headers = call("/api/v1/auth/login/", {"username": actor.username, "password": password}, data["data"]["csrfToken"], 429)
    assert "Retry-After" in headers
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user")
        role = cursor.fetchone()
        assert role == ("inventario_app", False, False, False)
    print(json.dumps({"resultado": "OK", "verificaciones_http": len(results), "uid": os.getuid(),
        "rol_db": {"nombre": role[0], "superusuario": role[1], "crea_bases": role[2], "crea_roles": role[3]},
        "fecha_utc": datetime.now(dt_timezone.utc).isoformat(), "casos": results}, ensure_ascii=False, indent=2))
finally:
    actor.is_active = False
    actor.save(update_fields=["is_active"])
