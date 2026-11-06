from rest_framework.test import APIClient

from .base import InventoryCase


class VersionedFlowTests(InventoryCase):
    def test_openapi_includes_all_versioned_routes_and_envelope(self):
        schema = self.client.get('/api/openapi.json').json()
        self.assertEqual(schema['openapi'], '3.1.0')
        self.assertEqual(schema['servers'][0]['url'], '/api/v1')
        self.assertEqual(set(schema['components']['schemas']['Envelope']['required']),
                         {'success', 'message', 'data', 'errors', 'meta'})
        for path in ['/assets/', '/assets/{asset_id}/', '/assets/{asset_id}/deliver/',
                     '/assets/{asset_id}/return/', '/custodians/', '/auth/login/']:
            self.assertIn(path, schema['paths'])
        page = self.client.get('/api/docs/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Activos: consulta actualizada')
        script = self.client.get('/api/docs/live.js')
        self.assertEqual(script.status_code, 200)
        self.assertIn(b'/api/v1/assets/?page=', script.content)

    def test_asset_cycle_and_legacy_contract(self):
        create = self.client.post('/api/v1/assets/', self.api_asset_data(), format='json')
        self.assertEqual(create.status_code, 201, create.content)
        self.assertEqual(set(create.json()), {'success', 'message', 'data', 'errors', 'meta'})
        asset = create.json()['data']
        self.assertTrue(create.json()['success'])
        self.assertIsNone(create.json()['errors'])
        listed = self.client.get('/api/v1/assets/', {'search': asset['code']})
        self.assertEqual(listed.json()['data']['results'][0]['id'], asset['id'])
        self.assertEqual(self.client.get(f"/api/v1/assets/{asset['id']}/").json()['data']['code'], asset['code'])
        custodian = self.client.post('/api/v1/custodians/', {'full_name': 'Docente de prueba', 'email': 'docente@example.org'}, format='json').json()['data']
        delivery = self.client.post(f"/api/v1/assets/{asset['id']}/deliver/", {'expected_revision': asset['revision'], 'custodian_id': custodian['id'], 'destination': 'Aula'}, format='json')
        self.assertEqual(delivery.status_code, 201, delivery.content)
        assigned = delivery.json()['data']['asset']
        self.assertEqual(assigned['assignment'], 'asignado')
        returned = self.client.post(f"/api/v1/assets/{asset['id']}/return/", {'expected_revision': assigned['revision'], 'condition': 'operativo', 'reception_location': 'Bodega'}, format='json')
        self.assertEqual(returned.status_code, 201, returned.content)
        self.assertEqual(returned.json()['data']['asset']['assignment'], 'disponible')
        legacy = self.client.get(f"/api/assets/{asset['id']}/").json()
        self.assertEqual(legacy['code'], asset['code'])
        self.assertNotIn('success', legacy)

    def test_errors_permissions_and_not_found_have_envelope(self):
        bad = self.client.post('/api/v1/assets/', {}, format='json')
        self.assertEqual(bad.status_code, 400)
        self.assertFalse(bad.json()['success'])
        self.assertIsNone(bad.json()['data'])
        self.assertIsInstance(bad.json()['errors'], dict)
        missing = self.client.get('/api/v1/assets/999999/')
        self.assertEqual(missing.status_code, 404)
        self.assertFalse(missing.json()['success'])
        no_route = self.client.get('/api/v1/inexistente/')
        self.assertEqual(no_route.status_code, 404)
        self.assertFalse(no_route.json()['success'])
        anonymous = APIClient().get('/api/v1/assets/')
        self.assertEqual(anonymous.status_code, 403)
        self.assertFalse(anonymous.json()['success'])

    def test_versioned_detail_rejects_undocumented_edit(self):
        asset = self.new_asset()
        response = self.client.patch(f"/api/v1/assets/{asset['id']}/", {'name': 'Otro'}, format='json')
        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.json()['success'])
        self.assertEqual(self.client.get(f"/api/assets/{asset['id']}/").json()['name'], asset['name'])

    def test_csrf_failure_returns_envelope_and_does_not_write(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        denied = client.post('/api/v1/assets/', self.api_asset_data(), format='json')
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(denied.json()['success'])
        self.assertEqual(denied.json()['errors']['code'], 'csrf_failed')

    def test_session_csrf_and_versioned_write(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        csrf = client.get('/api/v1/auth/csrf/')
        self.assertEqual(csrf.status_code, 200)
        token = csrf.json()['data']['csrfToken']
        created = client.post('/api/v1/assets/', self.api_asset_data(), format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(created.status_code, 201, created.content)
        self.assertTrue(created.json()['success'])
