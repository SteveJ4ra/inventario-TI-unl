"""Cobertura del contrato completo, permisos y estados observados por v1."""
import json
import re
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import DatabaseError
from django.test import TestCase
from rest_framework.test import APIClient
from jsonschema import Draft202012Validator
from inventory.openapi_v1 import SCHEMA
from inventory.observability import JsonRequestFormatter
from inventory.urls import urlpatterns
from .base import InventoryCase


class ContractClient(APIClient):
    """Verifica las respuestas reales de los casos, no una copia de los tipos."""
    def generic(self, method, path, *args, **kwargs):
        response=super().generic(method, path, *args, **kwargs)
        if method.upper() != 'HEAD' and path.startswith('/api/v1/') and 'application/json' in response.get('Content-Type',''):
            relative=path.split('?')[0].removeprefix('/api/v1')
            matched=next((pattern for pattern in SCHEMA['paths'] if re.fullmatch(re.sub(r'{[^}]+}',r'[^/]+',pattern),relative)),None)
            operation=SCHEMA['paths'].get(matched,{}).get(method.lower())
            if operation:
                assert str(response.status_code) in operation['responses'], (method,path,response.status_code)
                target=operation['responses'][str(response.status_code)]['content']['application/json']['schema']
                Draft202012Validator({'components':SCHEMA['components'],**target}).validate(response.json())
        return response


class CompleteV1Tests(InventoryCase):
    def setUp(self):
        super().setUp()
        self.client=ContractClient()
        self.client.force_authenticate(self.actor)

    def test_every_route_and_method_has_a_contract(self):
        actual={}
        for route in urlpatterns:
            path=re.sub(r'<[^:>]+:([^>]+)>',r'{\1}',str(route.pattern))
            actual['/'+path]={method for method in ['get','post','put','patch','delete'] if hasattr(route.callback.view_class,method)}
        self.assertEqual({path:set(methods) for path,methods in SCHEMA['paths'].items()},actual)
        def refs(value):
            if isinstance(value,dict):
                if '$ref' in value:
                    self.assertIn(value['$ref'].split('/')[-1],SCHEMA['components']['schemas'])
                for child in value.values(): refs(child)
            elif isinstance(value,list):
                for child in value: refs(child)
        refs(SCHEMA)
        json.dumps(SCHEMA)

    def test_versioned_audited_edit_and_read_only_fields(self):
        asset=self.new_asset()
        edited=self.client.patch(f"/api/v1/assets/{asset['id']}/",{'expected_revision':asset['revision'],'reason':'Corregir nombre','name':'Portátil corregido'},format='json')
        self.assertEqual(edited.status_code,200,edited.content)
        asset=edited.json()['data']
        self.assertEqual(asset['name'],'Portátil corregido')
        bad=self.client.patch(f"/api/v1/assets/{asset['id']}/",{'expected_revision':asset['revision'],'reason':'Intento inválido','assignment':'asignado'},format='json')
        self.assertEqual(bad.status_code,400)
        history=self.client.get(f"/api/v1/assets/{asset['id']}/history/").json()['data']
        self.assertEqual(history[0]['data']['reason'],'Corregir nombre')
        self.assertEqual(self.client.get(f"/api/assets/{asset['id']}/").json()['name'],asset['name'])

    def test_maintenance_blocks_delivery_and_closes_with_confirmation(self):
        asset=self.new_asset(); person=self.person()
        start=self.client.post(f"/api/v1/assets/{asset['id']}/maintenance/",{'expected_revision':asset['revision'],'description':'Revisión','workshop_location':'Taller'},format='json')
        self.assertEqual(start.status_code,201,start.content)
        event=start.json()['data']
        denied=self.client.post(f"/api/v1/assets/{asset['id']}/deliver/",{'expected_revision':event['revision'],'custodian_id':person['id'],'destination':'Aula'},format='json')
        self.assertEqual(denied.status_code,409)
        data={'expected_revision':event['revision'],'result':'Revisión realizada','receiving_location':event['previous_location'],'location_confirmed':False}
        url=f"/api/v1/maintenance/{event['id']}/close/"
        self.assertEqual(self.client.post(url,data,format='json').status_code,400)
        data['location_confirmed']=True
        closed=self.client.post(url,data,format='json')
        self.assertEqual(closed.status_code,200,closed.content)
        self.assertEqual(closed.json()['data']['receiving_location'],asset['location'])

    def test_incident_alert_and_license_quantity_validation(self):
        asset=self.new_asset()
        report=self.client.post(f"/api/v1/assets/{asset['id']}/incidents/",{'expected_revision':asset['revision'],'type':'damage','description':'Rayón superficial'},format='json')
        self.assertEqual(report.status_code,201,report.content)
        record=report.json()['data']
        listed=self.client.get(f"/api/v1/assets/{asset['id']}/incidents/")
        self.assertEqual(listed.json()['data'][0]['id'],record['id'])
        lot={'product_name':'Software de prueba','vendor':'Proveedor ficticio','license_model':'USER_SEAT','purchased_quantity':10,'in_use_quantity':4,'starts_on':'2025-01-01','ends_on':'2025-12-31'}
        created=self.client.post('/api/v1/license-lots/',lot,format='json')
        self.assertEqual(created.status_code,201,created.content)
        saved=created.json()['data'];self.assertEqual(saved['remaining_quantity'],6)
        self.assertEqual(saved['temporal_status'],'EXPIRED')
        bad=self.client.patch(f"/api/v1/license-lots/{saved['id']}/",{'expected_revision':saved['revision'],'in_use_quantity':11},format='json')
        self.assertEqual(bad.status_code,400)
        self.assertEqual(self.client.get(f"/api/license-lots/{saved['id']}/").json()['in_use_quantity'],4)

    def test_head_and_unsupported_methods_keep_http_semantics(self):
        asset=self.new_asset()
        response=self.client.head(f"/api/v1/assets/{asset['id']}/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,b'')
        denied=self.client.delete(f"/api/v1/assets/{asset['id']}/")
        self.assertEqual(denied.status_code,405)
        self.assertFalse(denied.json()['success'])
        self.assertEqual(self.client.get(f"/api/assets/{asset['id']}/").status_code,200)

    def test_operator_permissions_and_binary_exceptions(self):
        denied=self.client.get('/api/v1/operator/reviewers/')
        self.assertEqual(denied.status_code,403)
        self.assertFalse(denied.json()['success'])
        self.actor.groups.add(Group.objects.get_or_create(name='Operadores')[0])
        self.assertEqual(self.client.get('/api/v1/operator/reviewers/').status_code,200)
        asset=self.new_asset()
        with patch('inventory.views.build_asset_qr_url',return_value='https://example.org/assets/TI-000001'):
            qr=self.client.get(f"/api/v1/assets/{asset['id']}/qr.svg")
        self.assertEqual(qr.status_code,200)
        self.assertIn('image/svg+xml',qr['Content-Type'])
        csv=self.client.get('/api/v1/imports/templates/license_lots/')
        self.assertEqual(csv.status_code,200)
        self.assertTrue(csv.content.startswith(b'\xef\xbb\xbf'))
        self.assertIn('text/csv',csv['Content-Type'])
        self.assertEqual(APIClient().get('/api/v1/imports/templates/assets/').status_code,403)


class ObservabilityTests(TestCase):
    def test_readiness_and_failure_are_generic(self):
        ready=self.client.get('/health/ready/')
        self.assertEqual(ready.status_code,200)
        self.assertEqual(ready.json()['data'],{'status':'ready'})
        with patch('inventory.observability.connection.cursor',side_effect=DatabaseError('PASSWORD-MUST-NOT-LEAK')):
            failed=self.client.get('/health/ready/')
        self.assertEqual(failed.status_code,503)
        self.assertNotIn(b'PASSWORD',failed.content)

    def test_request_log_uses_template_without_url_values_or_body(self):
        with self.assertLogs('inventory.http',level='INFO') as captured:
            response=self.client.post('/api/v1/auth/login/?secret=DO-NOT-LOG',{'username':'PRIVATE-USER','password':'PRIVATE-PASSWORD'},content_type='application/json')
        record=captured.records[-1]
        payload=json.loads(JsonRequestFormatter().format(record))
        self.assertEqual(payload['route'],'api/v1/auth/login/')
        self.assertEqual(payload['request_id'],response['X-Request-ID'])
        self.assertEqual(len(payload['request_id']),32)
        self.assertNotIn('PRIVATE',json.dumps(payload))
        self.assertNotIn('DO-NOT-LOG',json.dumps(payload))
