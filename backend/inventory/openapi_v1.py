"""Esquema del flujo versionado de semana 3 y página de consulta Swagger UI."""
from pathlib import Path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET

ENVELOPE = {
    "type": "object", "required": ["success", "message", "data", "errors", "meta"],
    "properties": {"success": {"type": "boolean"}, "message": {"type": "string"},
                   "data": {}, "errors": {}, "meta": {"type": "object"}},
}
ID = {"name": "asset_id", "in": "path", "required": True, "schema": {"type": "integer", "minimum": 1}}
CSRF = {"name": "X-CSRFToken", "in": "header", "required": True, "schema": {"type": "string"},
        "description": "Token obtenido con GET /auth/csrf/; requerido para escrituras con sesión."}
def body(properties, required):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": properties, "required": required, "additionalProperties": False}}}}

def operation(summary, status=200, payload=None, params=None, public=False):
    error_content = {"application/json": {"schema": {"$ref": "#/components/schemas/Envelope"}}}
    result = {"summary": summary, "responses": {
        str(status): {"description": "Operación correcta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Envelope"}}}},
        "400": {"description": "Entrada inválida", "content": error_content}, "403": {"description": "Acceso o CSRF rechazado", "content": error_content},
        "404": {"description": "Recurso inexistente", "content": error_content}, "409": {"description": "Conflicto de identidad, revisión o estado", "content": error_content}},
        "parameters": list(params or []), "security": [] if public else [{"sessionCookie": []}]}
    if payload is not None:
        result['requestBody'] = payload
        result['parameters'].append(CSRF)
    return result

S = {"type": "string"}
I = {"type": "integer", "minimum": 1}
ASSET_FIELDS = {name: S for name in ['name','description','category','brand','model','serial_number','location','condition','item_value','acquired_on','date_unknown_reason']}
ASSET_FIELDS.update(faculty_id=I, acquisition_document_id=I)
ASSET_FIELDS.update(
    category={'type': 'string', 'enum': ['computadora_escritorio','portatil','monitor','impresora','equipo_red','periferico']},
    condition={'type': 'string', 'enum': ['operativo','averiado','en_reparacion']},
    acquired_on={'type': ['string','null'], 'format': 'date'},
    date_unknown_reason={'type': 'string', 'maxLength': 2000},
    item_value={'type': ['string','number'], 'description': 'Importe decimal con hasta 12 dígitos y dos decimales; los importes no positivos se rechazan con 409 según la política existente.'},
)
for name,limit in [('name',160),('description',2000),('brand',120),('model',120),('serial_number',160),('location',240)]:
    ASSET_FIELDS[name]={'type':'string','minLength':1,'maxLength':limit}
ASSET_REQUIRED = ['name','description','category','brand','model','serial_number','location','condition','item_value','faculty_id','acquisition_document_id']
SCHEMA = {"openapi": "3.1.0", "info": {"title": "Inventario TI: flujo de activos y custodia", "version": "1.0.0",
    "description": "Alcance v1 de semana 3. La facultad y el documento de adquisición deben existir; se administran mediante la API anterior. En el alta indique fecha de adquisición o motivo de desconocimiento, exclusivamente."},
    "servers": [{"url": "/api/v1"}], "paths": {
    "/auth/csrf/": {"get": operation("Obtener token CSRF", public=True)},
    "/auth/login/": {"post": operation("Iniciar sesión", payload=body({'username': S, 'password': S}, ['username','password']), public=True)},
    "/auth/me/": {"get": operation("Consultar sesión")},
    "/auth/logout/": {"post": operation("Cerrar sesión", params=[CSRF])},
    "/assets/": {"get": operation("Listar y buscar activos", params=[{"name": n,"in":"query","schema":{"type": "integer" if n in ['custodian','page'] else "string"}} for n in ['search','category','condition','situation','assignment','location','custodian','page']]),
                 "post": operation("Registrar activo",201,body(ASSET_FIELDS, ASSET_REQUIRED))},
    "/assets/{asset_id}/": {"get": operation("Consultar ficha", params=[ID])},
    "/assets/{asset_id}/movements/": {"get": operation("Consultar historial", params=[ID])},
    "/assets/{asset_id}/deliver/": {"post": operation("Entregar activo",201,body({'expected_revision': {'type':'integer','minimum':0},'custodian_id':I,'destination':S,'note':S}, ['expected_revision','custodian_id','destination']),[ID])},
    "/assets/{asset_id}/return/": {"post": operation("Devolver activo",201,body({'expected_revision': {'type':'integer','minimum':0},'condition':S,'reception_location':S,'note':S}, ['expected_revision','condition','reception_location']),[ID])},
    "/custodians/": {"get": operation("Listar custodios"), "post": operation("Registrar custodio",201,body({'full_name':S,'email':{'type':'string','format':'email'},'department':S},['full_name','email']))},
    }, "components": {"schemas": {"Envelope": ENVELOPE}, "securitySchemes": {"sessionCookie": {"type":"apiKey", "in":"cookie", "name":"sessionid"}}}}

SCHEMA['components']['schemas'].update({
    'Asset': {'type': 'object', 'required': ['id', 'code', 'name', 'assignment', 'revision'],
              'properties': {'id': I, 'code': S, 'name': S, 'assignment': {'type': ['string','null']},
                             'revision': {'type': 'integer', 'minimum': 0},
                             'condition': S, 'location': S,
                             'current_custodian': {'type': ['object', 'null']}}},
    'Custodian': {'type': 'object', 'required': ['id', 'full_name', 'email'],
                  'properties': {'id': I, 'full_name': S, 'email': S, 'department': S}},
    'MovementResult': {'type': 'object', 'required': ['asset', 'movement'],
                       'properties': {'asset': {'$ref': '#/components/schemas/Asset'},
                                      'movement': {'type': 'object'}}},
    'AssetPage': {'type': 'object', 'required': ['count', 'next', 'previous', 'results'],
                  'properties': {'count': {'type': 'integer'}, 'next': {'type': ['string', 'null']},
                                 'previous': {'type': ['string', 'null']},
                                 'results': {'type': 'array', 'items': {'$ref': '#/components/schemas/Asset'}}}},
})
asset_request=SCHEMA['paths']['/assets/']['post']['requestBody']['content']['application/json']
asset_request['schema']['oneOf']=[
    {'required':['acquired_on'], 'properties': {'acquired_on':{'type':'string','format':'date'},'date_unknown_reason':{'const':''}}},
    {'required':['date_unknown_reason'], 'properties': {'acquired_on':{'type':'null'},'date_unknown_reason':{'type':'string','pattern':r'\S'}}},
]
asset_request['example']={'name':'Portátil de prueba','description':'Equipo para demostración',
    'category':'portatil','brand':'Ejemplo','model':'A1','serial_number':'DEMO-001','location':'Bodega',
    'condition':'operativo','faculty_id':1,'acquisition_document_id':1,'item_value':'300.00','acquired_on':'2026-01-15'}
SCHEMA['paths']['/assets/{asset_id}/return/']['post']['requestBody']['content']['application/json']['schema']['properties']['condition']=ASSET_FIELDS['condition']
for parameter in SCHEMA['paths']['/assets/']['get']['parameters']:
    if parameter['name'] in ('page','custodian'):
        parameter['schema']['minimum']=1
    if parameter['name'] in ('category','condition'):
        parameter['schema']=ASSET_FIELDS[parameter['name']]
    if parameter['name']=='situation':
        parameter['schema']={'type':'string','enum':['disponible','asignado','no_localizado','baja']}
    if parameter['name']=='assignment':
        parameter['schema']={'type':'string','enum':['disponible','asignado']}
for path, method, status, schema in [
    ('/assets/', 'get', '200', 'AssetPage'), ('/assets/', 'post', '201', 'Asset'),
    ('/assets/{asset_id}/', 'get', '200', 'Asset'),
    ('/assets/{asset_id}/deliver/', 'post', '201', 'MovementResult'),
    ('/assets/{asset_id}/return/', 'post', '201', 'MovementResult'),
    ('/custodians/', 'post', '201', 'Custodian'),
]:
    output = SCHEMA['paths'][path][method]['responses'][status]['content']['application/json']
    output['schema'] = {'allOf': [{'$ref': '#/components/schemas/Envelope'},
                                  {'type': 'object', 'properties': {'data': {'$ref': '#/components/schemas/' + schema}}}]}

# No se anuncian errores que no tengan un escenario identificado para la operación.
for path, method, allowed in [
    ('/auth/csrf/', 'get', ()), ('/auth/login/', 'post', ('400', '403')),
    ('/auth/me/', 'get', ('403',)), ('/auth/logout/', 'post', ('403',)),
    ('/assets/', 'get', ('400', '403')), ('/assets/', 'post', ('400', '403', '409')),
    ('/assets/{asset_id}/', 'get', ('403', '404')),
    ('/assets/{asset_id}/movements/', 'get', ('403', '404')),
    ('/assets/{asset_id}/deliver/', 'post', ('400', '403', '404', '409')),
    ('/assets/{asset_id}/return/', 'post', ('400', '403', '404', '409')),
    ('/custodians/', 'get', ('403',)), ('/custodians/', 'post', ('400', '403', '409')),
]:
    responses = SCHEMA['paths'][path][method]['responses']
    for code in ('400', '403', '404', '409'):
        if code not in allowed:
            responses.pop(code, None)

SCHEMA['paths']['/auth/login/']['post']['responses']['429'] = {
    'description': 'Se agotaron cinco fallos por combinación de cuenta e IP en una ventana de quince minutos. Esperar el plazo indicado.',
    'headers': {'Retry-After': {'description': 'Segundos restantes de la ventana.', 'schema': {'type':'integer','minimum':1}}},
    'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Envelope'}}},
}
SCHEMA['info']['description'] += ' Seguridad de semana 4: sesión con vencimiento absoluto de treinta minutos, sin renovación por consultas; cinco fallos de acceso por cuenta e IP en quince minutos y rechazo posterior con 429.'

SCHEMA['paths']['/auth/login/']['post']['requestBody']['content']['application/json']['schema']['properties']['username'] = {'type':'string','maxLength':150,'pattern':r'^[^\u0000]*$'}

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
