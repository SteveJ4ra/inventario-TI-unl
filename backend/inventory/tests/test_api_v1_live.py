import http.cookiejar
import json
from datetime import date
from decimal import Decimal
from urllib.request import HTTPCookieProcessor, Request, build_opener

from django.test import LiveServerTestCase

from inventory.models import AcquisitionDocument, Faculty
from .base import asset_data, manager


class LiveVersionedFlowTests(LiveServerTestCase):
    def test_session_csrf_create_deliver_and_return_over_http(self):
        actor = manager('gestor-live')
        actor.set_password('solo-prueba-local-482')
        actor.save()
        faculty = Faculty.objects.create(name='Facultad de prueba HTTP')
        doc = AcquisitionDocument.objects.create(source='PURCHASE', reference='FACT-HTTP',
            document_date=date(2026,1,15), supplier='Proveedor de prueba',
            invoice_total=Decimal('1000.00'), created_by=actor)
        opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

        def call(path, payload=None, csrf=None):
            headers={'Accept':'application/json'}
            if csrf:
                headers['X-CSRFToken']=csrf
            body=None
            if payload is not None:
                headers['Content-Type']='application/json'
                body=json.dumps(payload).encode()
            request=Request(self.live_server_url+path, data=body, headers=headers)
            with opener.open(request,timeout=10) as response:
                return response.status, json.load(response)

        _, csrf=call('/api/v1/auth/csrf/')
        token=csrf['data']['csrfToken']
        status,_=call('/api/v1/auth/login/', {'username':'gestor-live','password':'solo-prueba-local-482'}, token)
        self.assertEqual(status,200)
        _, csrf=call('/api/v1/auth/csrf/')
        token=csrf['data']['csrfToken']
        _, person=call('/api/v1/custodians/', {'full_name':'Custodio de prueba','email':'custodio@example.org'},token)
        payload=asset_data(faculty_id=faculty.pk, acquisition_document_id=doc.pk, item_value='300.00', acquired_on='2026-01-15')
        status, result=call('/api/v1/assets/',payload,token)
        self.assertEqual(status,201)
        asset=result['data']
        status, item=call(f"/api/v1/assets/{asset['id']}/")
        self.assertEqual((status,item['data']['code']),(200,asset['code']))
        status, delivery=call(f"/api/v1/assets/{asset['id']}/deliver/", {'expected_revision':asset['revision'],'custodian_id':person['data']['id'],'destination':'Aula'},token)
        self.assertEqual(status,201)
        status, returned=call(f"/api/v1/assets/{asset['id']}/return/", {'expected_revision':delivery['data']['asset']['revision'],'condition':'operativo','reception_location':'Bodega'},token)
        self.assertEqual(status,201)
        self.assertEqual(returned['data']['asset']['assignment'],'disponible')
        self.assertIsNone(returned['data']['asset']['current_custodian'])
