"""Contrato OpenAPI completo y explorador interactivo de la API."""
from pathlib import Path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from .openapi_contract import build_schema

SCHEMA = build_schema()

@require_GET
def schema(request):
    return JsonResponse(SCHEMA)

@require_GET
def swagger_ui(request):
    return HttpResponse('''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>API Inventario TI</title><link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css"><style>body{margin:0;font-family:Arial,sans-serif;color:#263238}.live{max-width:1460px;margin:24px auto;padding:0 20px}.live-table{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #d7e0e3;padding:8px;text-align:left}button{padding:8px 12px;cursor:pointer}</style></head><body><section class="live" aria-labelledby="live-title"><h1 id="live-title">Activos: consulta actualizada</h1><p>La página mostrada se consulta de nuevo cada cinco segundos mientras esta ventana está visible.</p><p>Para acceder, inicia sesión como gestor. Puedes usar las operaciones de autenticación de Swagger con tu token CSRF o iniciar sesión en la aplicación de inventario.</p><button type="button" id="live-refresh">Actualizar ahora</button><p id="live-status" role="status" aria-live="polite">Consultando activos…</p><div class="live-table"><table><thead><tr><th>Código</th><th>Nombre</th><th>Condición</th><th>Situación</th><th>Asignación</th><th>Ubicación</th></tr></thead><tbody id="live-assets"></tbody></table></div><p><button type="button" id="live-previous" disabled>Anterior</button> <span id="live-page">Página 1</span> <button type="button" id="live-next" disabled>Siguiente</button></p></section><div id="swagger-ui"></div><script src="/api/docs/live.js"></script><script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script><script>SwaggerUIBundle({url:'/api/openapi.json',dom_id:'#swagger-ui',withCredentials:true});</script></body></html>''')

@require_GET
def live_script(request):
    script = Path(__file__).with_name('docs_live.js').read_text(encoding='utf-8')
    return HttpResponse(script, content_type='application/javascript; charset=utf-8')
