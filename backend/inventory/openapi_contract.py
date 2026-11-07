"""Contrato derivado de serializadores reales y registro explícito de operaciones.

Los diccionarios de auditoría son instantáneas extensibles. No se anuncian
propiedades inventadas para dichos datos. No requiere conexión a la base.
"""
import re
from copy import deepcopy
from rest_framework import serializers as drf
from . import serializers as s
from . import retirement_serializers as r

S = {"type": "string"}
I = {"type": "integer", "minimum": 1}
N = {"type": "integer", "minimum": 0}
OBJ = {"type": "object", "additionalProperties": True}


def ref(name):
    return {"$ref": "#/components/schemas/" + name}


def array(item):
    return {"type": "array", "items": item}


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def field_schema(field, output=False):
    if isinstance(field, drf.ReadOnlyField):
        result = {}
    elif isinstance(field, drf.ListSerializer):
        result = array(serializer_schema(field.child, output))
    elif isinstance(field, drf.BaseSerializer):
        result = serializer_schema(field, output)
    elif isinstance(field, drf.ChoiceField):
        result = {"type": "string", "enum": list(field.choices)}
    elif isinstance(field, drf.BooleanField):
        result = {"type": "boolean"}
    elif isinstance(field, drf.IntegerField):
        result = {"type": "integer"}
    elif isinstance(field, drf.DecimalField):
        result = {"type": "string", "pattern": r"^-?\d+(\.\d{1,2})?$"}
        if not output:
            result = {"anyOf": [result, {"type": "number"}],
                      "description": "Decimal finito; precisión validada por el servidor. Importes de adquisición estrictamente positivos (409 si no)."}
    elif isinstance(field, drf.DateTimeField):
        result = {"type": "string", "format": "date-time"}
    elif isinstance(field, drf.DateField):
        result = {"type": "string", "format": "date"}
    elif isinstance(field, drf.DictField):
        child = getattr(field, "child", None)
        result = {"type": "object", "additionalProperties": field_schema(child, output) if child and type(child) is not type(drf.DictField().child) else True}
    elif isinstance(field, drf.ListField):
        result = array(field_schema(field.child, output))
    elif isinstance(field, (drf.JSONField, drf.SerializerMethodField)):
        result = {}  # Instantáneas/valores calculados se especializan más abajo.
    elif isinstance(field, drf.CharField):
        result = {"type": "string"}
        if isinstance(field, drf.EmailField):
            result["format"] = "email"
        for attribute, key in [("max_length", "maxLength"), ("min_length", "minLength")]:
            value = getattr(field, attribute, None)
            if value is not None:
                result[key] = value
        if not output and not getattr(field, "allow_blank", True):
            result["minLength"] = max(1, result.get("minLength", 0))
    else:
        result = {}
    for attribute, key in [("min_value", "minimum"), ("max_value", "maximum")]:
        value = getattr(field, attribute, None)
        if isinstance(value, (int, float)):
            result[key] = value
    if getattr(field, "write_only", False):
        result["writeOnly"] = True
    if field.allow_null or (output and field.default is None):
        result = nullable(result)
    return result


def serializer_schema(serializer, output=False):
    instance = serializer() if isinstance(serializer, type) else serializer
    fields = {name: field for name, field in instance.fields.items()
              if not (output and field.write_only) and not (not output and field.read_only)}
    properties = {name: field_schema(field, output) for name, field in fields.items()}
    if output:
        model = getattr(getattr(instance, "Meta", None), "model", None)
        for name, field in fields.items():
            if model is not None and isinstance(field, drf.ReadOnlyField):
                from django.core.exceptions import FieldDoesNotExist
                try:
                    model_field = model._meta.get_field(field.source or name)
                except FieldDoesNotExist:
                    continue
                if model_field.is_relation:
                    properties[name] = nullable(I) if model_field.null else deepcopy(I)
    return obj(properties, [name for name, field in fields.items() if output or field.required])


def build_schema():
    inputs = [s.AcquisitionAssetInput, s.AssetEditInput, s.CustodianInput, s.CustodianEditInput,
              s.AcquisitionDocumentInput, s.DocumentEditInput, s.FacultyInput, s.FacultyChangeInput,
              s.DeliveryInput, s.ReturnInput, s.ConditionInput, s.RectificationInput,
              s.IncidentInput, s.IncidentResolutionInput, s.RecoveryInput,
              s.MaintenanceStartInput, s.MaintenanceCloseInput, s.LicenseLotInput, s.LicenseLotPatchInput,
              r.NormalRetirementInput, r.RetirementRequestInput, r.RetirementDecisionInput,
              r.RetirementReassignmentInput, r.ReviewerCreateInput, r.ReviewerDeactivateInput,
              r.ReviewerPasswordChangeInput]
    outputs = [s.AssetOutput, s.CustodianOutput, s.MovementOutput, s.IncidentOutput,
               s.RecoveryOutput, s.MaintenanceDetail, s.HistoryEntry, s.FacultyOutput,
               s.AcquisitionDocumentOutput, s.LicenseLotOutput, s.LicenseLotAuditOutput]
    schemas = {cls.__name__: serializer_schema(cls) for cls in inputs}
    schemas.update({cls.__name__: serializer_schema(cls, True) for cls in outputs})
    schemas['Envelope'] = obj({'success': {'type':'boolean'}, 'message': S,
                               'data': {}, 'errors': {}, 'meta': OBJ})
    actor = obj({'id': I, 'username': S})
    for name, fields in {
        'AssetOutput': ['created_by'], 'AcquisitionDocumentOutput': ['created_by'],
        'MovementOutput': ['actor'], 'LicenseLotOutput': ['created_by'],
        'LicenseLotAuditOutput': ['actor'], 'IncidentOutput': ['reported_by'],
    }.items():
        for field in fields:
            schemas[name]['properties'][field] = deepcopy(actor)
            if name in ('MovementOutput', 'LicenseLotAuditOutput'):
                schemas[name]['properties'][field]['properties']['recorded_label'] = S
                schemas[name]['properties'][field]['required'].append('recorded_label')
    asset = schemas['AssetOutput']['properties']
    for name in ['active_maintenance_id', 'rectifiable_movement_id']:
        asset[name] = nullable(I)
    asset['current_custodian'] = nullable(ref('CustodianOutput'))
    asset['acquisition'] = nullable(OBJ)
    schemas['MovementOutput']['properties']['rectified_by_id'] = nullable(I)
    schemas['IncidentOutput']['properties']['resolved_by'] = nullable(actor)
    schemas['MovementResult'] = obj({'asset': ref('AssetOutput'), 'movement': ref('MovementOutput')})
    schemas['Session'] = obj({'id': I, 'username': S, 'permissions': array(S), 'must_change_password': {'type':'boolean'}})
    schemas['Detail'] = obj({'detail': S})
    schemas['LoginInput'] = obj({'username': {'type':'string','minLength':1,'maxLength':150,'pattern':r'^[^\u0000]*$'},
                                'password': {'type':'string','minLength':1,'writeOnly':True}})
    schemas['RetirementRequest'] = obj({'id': I, 'asset_id': I, 'asset_code': S, 'reason': S,
        'status': {'type':'string','enum':['pending','approved','rejected','cancelled']},
        'reviewer_id': I, 'expected_revision': N, 'context': OBJ, 'history': array(OBJ)})
    schemas['Retired'] = obj({'id':I, 'movement_id':I})
    schemas['Decision'] = obj({'id':I, 'outcome':S})
    schemas['Reviewer'] = obj({'id':I,'username':S,'faculty_id':I,'active':{'type':'boolean'}})
    schemas['ReviewerCreated'] = obj({'id':I,'username':S,'faculty_id':I,'must_change_password':{'const':True}})
    schemas['ReviewerDisabled'] = obj({'id':I,'active':{'const':False}})
    schemas['Options'] = obj({name: array(obj({'value':S,'label':S})) for name in ['categories','conditions','assignments']} | {'locations':array(S)})
    for name, item in [('AssetPage','AssetOutput'),('LicensePage','LicenseLotOutput'),('LicenseHistoryPage','LicenseLotAuditOutput')]:
        schemas[name] = obj({'count':N,'next':nullable(S),'previous':nullable(S),'results':array(ref(item))})
    schemas['Batch'] = obj({'batch_id':{'type':'string','format':'uuid'},'kind':{'enum':['assets','license_lots']},
        'schema_version':S,'state':S,'content_hash':{'type':'string','pattern':'^[0-9a-f]{64}$'},
        'summary':OBJ,'errors':array(OBJ),'rows':array(OBJ),'row_count':N,'page':I,
        'next':nullable(S),'previous':nullable(S),'created_at':{'type':'string','format':'date-time'},
        'expires_at':{'type':'string','format':'date-time'},'confirmed_at':nullable({'type':'string','format':'date-time'}),
        'applied_at':nullable({'type':'string','format':'date-time'}),'applied_result':nullable(OBJ)})
    schemas['HashInput'] = obj({'content_hash':{'type':'string','pattern':'^[0-9a-f]{64}$'}})
    schemas['Upload'] = obj({'kind':{'type':'string','enum':['assets','license_lots']},
        'schema_version':{'type':'string','enum':['assets-v1','license-lots-v1']},
        'file':{'type':'string','format':'binary'}})
    # Condiciones entre campos que no se deducen de los tipos DRF.
    date_rule = [
        {'required':['acquired_on'],'properties':{'acquired_on':{'type':'string','format':'date'},'date_unknown_reason':{'const':''}}},
        {'required':['date_unknown_reason'],'properties':{'acquired_on':{'type':'null'},'date_unknown_reason':{'type':'string','pattern':r'\S'}}},
    ]
    schemas['AcquisitionAssetInput']['oneOf'] = date_rule
    schemas['AcquisitionAssetInput']['description'] = 'Disponible y sin custodio al crearse. Facultad y documento existentes. Código TI automático; identidad marca/modelo/serie normalizada y única.'
    purchase = deepcopy(schemas['AcquisitionDocumentInput'])
    purchase['properties']['source']={'const':'PURCHASE'}
    purchase['properties'].pop('support_type')
    purchase['required'] += ['document_date','supplier','invoice_total']
    purchase['properties']['document_date']={'type':'string','format':'date'}
    purchase['properties']['supplier']={'type':'string','minLength':1,'maxLength':160}
    purchase['properties']['invoice_total']={'anyOf':[{'type':'string','pattern':r'^\d+(\.\d{1,2})?$'},{'type':'number'}]}
    donation = deepcopy(schemas['AcquisitionDocumentInput'])
    donation['properties']['source']={'const':'DONATION'}
    for field in ['supplier','invoice_total']:
        donation['properties'].pop(field)
    donation['required'] += ['support_type']
    donation['properties']['support_type']={'type':'string','minLength':1,'maxLength':160}
    donation['properties']['items'] = array(serializer_schema(s.ExistingDonationItemInput))
    schemas['AcquisitionDocumentInput'] = {'oneOf':[purchase,donation]}
    for name, field in [('RecoveryInput','inspection_confirmed'),('MaintenanceCloseInput','location_confirmed')]:
        schemas[name]['properties'][field]={'const':True}
    schemas['RetirementDecisionInput']['allOf']=[{'if':{'properties':{'decision':{'const':'reject'}}},
        'then':{'required':['reason'],'properties':{'reason':{'type':'string','pattern':r'\S'}}}}]
    schemas['LicenseLotPatchInput']['description']='Revisión obligatoria y al menos un campo editable. En uso <= compradas; fin >= inicio. Remanentes se conservan aunque el lote venza.'
    paths = {}
    def add(path, method, summary, output, input=None, status=200, role='manager', query=None, media='application/json'):
        parameters=[]
        for name in re.findall(r'{([^}]+)}',path):
            schema = {'type':'string','format':'uuid'} if name=='batch_id' else S if name in ['code','kind'] else I
            parameters.append({'name':name,'in':'path','required':True,'schema':schema})
        if query:
            fields=serializer_schema(query)['properties'] if isinstance(query,type) else query
            parameters += [{'name':name,'in':'query','schema':schema} for name,schema in fields.items()]
        responses={}
        def response(code, description, data=None):
            schema={'allOf':[ref('Envelope'),{'type':'object','properties':{'data':data or {}}}]} if int(code)<400 else ref('Envelope')
            responses[str(code)]={'description':description,'content':{'application/json':{'schema':schema}}}
        response(status,'Operación correcta', ref(output) if isinstance(output,str) else output)
        if role != 'public': response(403,'Sin permiso, sesión vencida o CSRF ausente')
        if method!='get' or query: response(400,'Campos o formato inválidos')
        if '{' in path: response(404,'Recurso inexistente o no visible para la cuenta')
        if method in ('post','patch') and not path.startswith('/auth/'):
            response(409,'Conflicto de revisión, identidad o regla de negocio')
        operation={'operationId':method+'_'+re.sub(r'[^a-zA-Z0-9]+','_',path).strip('_'),
            'summary':summary,'tags':[path.strip('/').split('/')[0]],
            'description':'Acceso: '+role+'. JSON con envoltura uniforme; los cambios conservan la auditoría de dominio.',
            'security':[] if role=='public' else [{'sessionCookie':[]}], 'parameters':parameters,'responses':responses}
        if method in ('post','patch'):
            parameters.append({'name':'X-CSRFToken','in':'header','required':True,'schema':S,
                'description':'Obtener csrfToken en /auth/csrf/. Enviar también las cookies de la misma sesión.'})
        if input:
            operation['requestBody']={'required':True,'content':{media:{'schema':ref(input)}}}
        paths.setdefault(path,{})[method]=operation
        return operation
    add('/auth/csrf/','get','Obtener token CSRF',obj({'csrfToken':S}),role='public')
    login=add('/auth/login/','post','Iniciar sesión','Session','LoginInput',role='public')
    login['responses']['403']={'description':'Credenciales incorrectas, cuenta no autorizada o CSRF inválido','content':{'application/json':{'schema':ref('Envelope')}}}
    login['responses']['429']={'description':'Cinco fallos por cuenta e IP en quince minutos; esperar el plazo indicado.',
        'headers':{'Retry-After':{'schema':I,'description':'Segundos restantes'}},'content':{'application/json':{'schema':ref('Envelope')}}}
    add('/auth/me/','get','Consultar sesión','Session',role='cuenta autorizada')
    add('/auth/logout/','post','Cerrar sesión','Detail',role='cuenta autorizada')
    add('/auth/change-password/','post','Cambiar contraseña de revisor','Detail','ReviewerPasswordChangeInput',role='reviewer (incluye contraseña temporal)')
    add('/assets/','get','Buscar activos','AssetPage',query=s.QueryInput)
    add('/assets/','post','Registrar activo','AssetOutput','AcquisitionAssetInput',201)
    add('/assets/{asset_id}/','get','Consultar ficha','AssetOutput')
    add('/assets/{asset_id}/','patch','Corregir datos descriptivos con auditoría','AssetOutput','AssetEditInput')
    add('/assets/by-code/{code}/','get','Consultar por código TI','AssetOutput')
    qr=add('/assets/{asset_id}/qr.svg','get','Descargar QR autenticado',{})
    qr['responses']['200']={'description':'SVG descargable. Excepción binaria a la envoltura JSON; contiene enlace interno sin datos personales.',
        'content':{'image/svg+xml':{'schema':{'type':'string'}}}}
    for endpoint, summary, output in [('movements','Consultar movimientos','MovementOutput'),('history','Consultar historial consolidado','HistoryEntry'),('incidents','Consultar novedades','IncidentOutput')]:
        add('/assets/{asset_id}/'+endpoint+'/', 'get',summary,array(ref(output)))
    for endpoint, summary, input in [('deliver','Entregar activo','DeliveryInput'),('return','Devolver activo','ReturnInput'),('condition','Cambiar condición','ConditionInput'),('rectify','Rectificar último movimiento','RectificationInput')]:
        add('/assets/{asset_id}/'+endpoint+'/', 'post',summary,'MovementResult',input,201)
    add('/assets/{asset_id}/incidents/','post','Reportar daño, pérdida o robo','IncidentOutput','IncidentInput',201)
    add('/incidents/{incident_id}/resolve/','post','Resolver novedad','IncidentOutput','IncidentResolutionInput')
    add('/assets/{asset_id}/recover/','post','Registrar recuperación inspeccionada','RecoveryOutput','RecoveryInput',201)
    add('/assets/{asset_id}/maintenance/','post','Iniciar mantenimiento','MaintenanceDetail','MaintenanceStartInput',201)
    add('/maintenance/{maintenance_id}/','get','Consultar mantenimiento','MaintenanceDetail')
    add('/maintenance/{maintenance_id}/close/','post','Cerrar mantenimiento','MaintenanceDetail','MaintenanceCloseInput')
    add('/custodians/','get','Listar custodios',array(ref('CustodianOutput')))
    add('/custodians/','post','Registrar custodio','CustodianOutput','CustodianInput',201)
    add('/custodians/{custodian_id}/','patch','Corregir custodio sin alterar instantáneas históricas','CustodianOutput','CustodianEditInput')
    add('/options/','get','Consultar opciones de inventario','Options')
    add('/faculties/','get','Listar facultades activas',array(ref('FacultyOutput')),role='manager u operator')
    add('/operator/faculties/','get','Listar todas las facultades',array(ref('FacultyOutput')),role='operator')
    add('/operator/faculties/','post','Crear facultad','FacultyOutput','FacultyInput',201,role='operator')
    schemas['FacultyPatchInput']=deepcopy(schemas['FacultyInput']);schemas['FacultyPatchInput']['required']=[]
    add('/operator/faculties/{faculty_id}/','patch','Actualizar facultad','FacultyOutput','FacultyPatchInput',role='operator')
    add('/operator/assets/{asset_id}/faculty/','patch','Cambiar facultad con auditoría','AssetOutput','FacultyChangeInput',role='operator')
    add('/acquisitions/','post','Registrar factura o respaldo compartido','AcquisitionDocumentOutput','AcquisitionDocumentInput',201)
    add('/acquisitions/{document_id}/','get','Consultar adquisición','AcquisitionDocumentOutput')
    add('/acquisitions/{document_id}/','patch','Corregir documento compartido con control de instantáneas','AcquisitionDocumentOutput','DocumentEditInput')
    add('/license-lots/','get','Consultar lotes de licencias','LicensePage',query=s.LicenseLotQuery)
    add('/license-lots/','post','Registrar lote de licencias','LicenseLotOutput','LicenseLotInput',201)
    add('/license-lots/{lot_id}/','get','Consultar lote','LicenseLotOutput')
    add('/license-lots/{lot_id}/','patch','Actualizar lote con auditoría','LicenseLotOutput','LicenseLotPatchInput')
    add('/license-lots/{lot_id}/history/','get','Consultar historial del lote','LicenseHistoryPage',query=s.LicenseHistoryQuery)
    add('/assets/{asset_id}/retire/','post','Dar de baja activo Disponible','Retired','NormalRetirementInput',201)
    add('/assets/{asset_id}/retirement-requests/','get','Consultar solicitudes de baja',array(ref('RetirementRequest')))
    add('/assets/{asset_id}/retirement-requests/','post','Solicitar baja de No localizado','RetirementRequest','RetirementRequestInput',201)
    add('/reviewer/retirement-requests/','get','Consultar solicitudes asignadas',array(ref('RetirementRequest')),role='reviewer (contraseña inicial cambiada)')
    add('/retirement-requests/{request_id}/decision/','post','Aprobar o rechazar solicitud asignada','Decision','RetirementDecisionInput',201,role='reviewer asignado de otra facultad')
    add('/retirement-requests/{request_id}/reassign/','post','Reasignar solicitud pendiente','RetirementRequest','RetirementReassignmentInput',role='operator')
    add('/operator/reviewers/','get','Listar revisores',array(ref('Reviewer')),role='operator')
    add('/operator/reviewers/','post','Crear revisor con contraseña temporal','ReviewerCreated','ReviewerCreateInput',201,role='operator')
    add('/operator/reviewers/{user_id}/','patch','Desactivar revisor sin solicitudes pendientes','ReviewerDisabled','ReviewerDeactivateInput',role='operator')
    template=add('/imports/templates/{kind}/','get','Descargar plantilla CSV',{},query={'schema_version':S})
    template['responses']['200']={'description':'CSV UTF-8 con BOM. Excepción de archivo a la envoltura JSON.', 'content':{'text/csv':{'schema':S}}}
    preview=add('/imports/previews/','post','Validar lote completo sin aplicar','Batch','Upload',201,media='multipart/form-data')
    preview['description']+=' Máximo 2.000.000 bytes y 2.000 filas por defecto; plantilla acorde al tipo; sin creación parcial.'
    add('/imports/{batch_id}/','get','Consultar vista previa propia','Batch',query={'page':I})
    add('/imports/{batch_id}/confirm/','post','Primera confirmación del mismo gestor','Batch','HashInput')
    apply=add('/imports/{batch_id}/apply/','post','Confirmar y aplicar lote atómicamente','Batch','HashInput',201)
    apply['responses']['200']=deepcopy(apply['responses']['201']);apply['responses']['200']['description']='Repetición idempotente del lote ya aplicado'
    add('/imports/{batch_id}/cancel/','post','Cancelar lote propio','Batch')
    for operation in [preview, apply, paths['/imports/{batch_id}/confirm/']['post']]:
        operation['responses']['503']={'description':'Proveedor no disponible; no se aplica el lote','content':{'application/json':{'schema':ref('Envelope')}}}
    preview['responses']['413']={'description':'Límite de bytes o filas excedido','content':{'application/json':{'schema':ref('Envelope')}}}
    return {'openapi':'3.1.0','info':{'title':'Inventario TI UNL - Backend completo','version':'1.1.0',
        'description':'API completa de 002-008. Sesión absoluta de 30 minutos, CSRF en escrituras y cinco fallos de acceso por cuenta/IP en quince minutos. Se conservan /api/ y su contrato histórico. Las respuestas JSON v1 usan success/message/data/errors/meta; SVG, CSV, HEAD y 204/304 conservan semántica HTTP. Revisiones y permisos se validan en servidor.'},
        'servers':[{'url':'/api/v1'}], 'paths':paths,
        'components':{'schemas':schemas,'securitySchemes':{'sessionCookie':{'type':'apiKey','in':'cookie','name':'sessionid'}}}}
