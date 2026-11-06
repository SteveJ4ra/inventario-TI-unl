from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.test import TransactionTestCase


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LoginLimitTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('gestor-seguridad', password='Solo-Prueba-2026!')
        self.user.groups.add(Group.objects.get_or_create(name='Gestores')[0])
        self.client=APIClient(enforce_csrf_checks=True)

    def login(self, password='incorrecta', route='/api/auth/login/', ip='127.0.0.1', forwarded=''):
        token=self.client.get('/api/auth/csrf/').json()['csrfToken']
        return self.client.post(route, {'username':self.user.username,'password':password},
            format='json',HTTP_X_CSRFTOKEN=token,REMOTE_ADDR=ip,HTTP_X_FORWARDED_FOR=forwarded)

    def test_sixth_failed_login_is_throttled_across_api_versions(self):
        for _ in range(5):
            self.assertEqual(self.login().status_code,400)
        result=self.login(route='/api/v1/auth/login/')
        self.assertEqual(result.status_code,429,result.content)
        self.assertIn('Retry-After',result)
        self.assertFalse(result.json()['success'])

    def test_block_does_not_accept_valid_password_or_forged_forwarded_ip(self):
        for _ in range(5): self.login()
        self.assertEqual(self.login(password='Solo-Prueba-2026!',forwarded='198.51.100.2').status_code,429)
        self.assertEqual(self.login(password='Solo-Prueba-2026!',ip='127.0.0.2').status_code,200)

    def test_expiry_allows_login_and_success_resets_failures(self):
        from datetime import timedelta
        from django.utils import timezone
        from inventory.models import LoginAttempt
        for _ in range(4): self.login()
        self.assertEqual(self.login(password='Solo-Prueba-2026!').status_code,200)
        self.assertEqual(LoginAttempt.objects.get().failures,0)
        for _ in range(5): self.login()
        LoginAttempt.objects.update(window_started=timezone.now()-timedelta(minutes=16))
        self.assertEqual(self.login(password='Solo-Prueba-2026!').status_code,200)

    def test_expired_counters_can_be_cleaned_without_removing_current(self):
        from datetime import timedelta
        from django.core.management import call_command
        from django.utils import timezone
        from inventory.models import LoginAttempt
        self.login()
        attempt=LoginAttempt.objects.get()
        self.assertEqual(len(attempt.key),64)
        LoginAttempt.objects.create(key='e'*64,failures=1,window_started=timezone.now()-timedelta(minutes=16))
        call_command('cleanup_login_attempts')
        self.assertEqual(list(LoginAttempt.objects.values_list('key',flat=True)),[attempt.key])

    def test_window_starts_with_first_failure_after_success(self):
        from datetime import timedelta
        from django.utils import timezone
        from inventory.models import LoginAttempt
        self.assertEqual(self.login(password='Solo-Prueba-2026!').status_code,200)
        LoginAttempt.objects.update(window_started=timezone.now()-timedelta(minutes=10))
        before=timezone.now()
        self.assertEqual(self.login().status_code,400)
        self.assertGreaterEqual(LoginAttempt.objects.get().window_started,before)

    def test_api_responses_prevent_shared_and_browser_caching(self):
        self.client.force_login(self.user)
        for route in ['/api/auth/me/','/api/v1/auth/me/','/api/assets/','/api/v1/assets/']:
            response=self.client.get(route)
            self.assertEqual(response.status_code,200,response.content)
            self.assertIn('no-store',response['Cache-Control'])
            self.assertIn('private',response['Cache-Control'])
            self.assertIn('Cookie',response['Vary'])

    def test_internal_error_has_generic_json_without_sensitive_detail(self):
        from unittest.mock import patch
        self.client.force_login(self.user)
        self.client.raise_request_exception=False
        with self.assertLogs('django.request',level='ERROR'), patch('inventory.views.assets',side_effect=RuntimeError('INTERNAL-DETAIL-TEST')):
            result=self.client.get('/api/v1/assets/')
        self.assertEqual(result.status_code,500)
        self.assertFalse(result.json()['success'])
        self.assertNotIn('INTERNAL-DETAIL-TEST',result.content.decode())

    def test_invalid_username_is_rejected_before_authentication(self):
        from inventory.models import LoginAttempt
        for username in ['\x00', 'x'*151]:
            token=self.client.get('/api/auth/csrf/').json()['csrfToken']
            result=self.client.post('/api/auth/login/',{'username':username,'password':'incorrecta'},
                format='json',HTTP_X_CSRFTOKEN=token)
            self.assertEqual(result.status_code,400)
        self.assertEqual(LoginAttempt.objects.count(),0)

    def test_session_expires_after_thirty_minutes_without_polling_extension(self):
        from django.utils import timezone
        from django.contrib.sessions.models import Session
        self.assertEqual(self.login(password='Solo-Prueba-2026!').status_code,200)
        session=self.client.session
        expiry=session.get_expiry_date()
        self.assertGreater((expiry-timezone.now()).total_seconds(),1790)
        self.assertLessEqual((expiry-timezone.now()).total_seconds(),1800)
        for _ in range(3):
            self.assertEqual(self.client.get('/api/v1/assets/').status_code,200)
            self.client.get('/api/auth/csrf/')
        self.assertEqual(self.client.session.get_expiry_date(),expiry)
        Session.objects.filter(session_key=session.session_key).update(expire_date=timezone.now())
        self.assertEqual(self.client.get('/api/v1/assets/').status_code,403)

    def test_deployment_expires_old_sessions_but_preserves_new_deadlines(self):
        from django.contrib.sessions.models import Session
        from django.core.management import call_command
        from django.utils import timezone
        legacy=APIClient()
        legacy.force_login(self.user)
        self.assertEqual(self.login(password='Solo-Prueba-2026!').status_code,200)
        call_command('expire_legacy_sessions')
        self.assertLessEqual(Session.objects.get(pk=legacy.session.session_key).expire_date,timezone.now())
        self.assertEqual(self.client.get('/api/auth/me/').status_code,200)


    def test_deployment_rejects_malformed_naive_and_excessive_deadlines(self):
        from datetime import timedelta
        from io import StringIO
        from django.contrib.sessions.models import Session
        from django.contrib.sessions.backends.db import SessionStore
        from django.core.management import call_command
        from django.utils import timezone
        from secrets import token_hex
        now=timezone.now()
        keys=[]
        for value in ['2026-99-99T00:00:00', '2026-11-06T12:00:00', (now+timedelta(days=1)).isoformat()]:
            key=token_hex(16)
            Session.objects.create(session_key=key,session_data=SessionStore().encode({'_session_expiry':value}),expire_date=now+timedelta(days=1))
            keys.append(key)
        call_command('expire_legacy_sessions',stdout=StringIO())
        self.assertFalse(Session.objects.filter(pk__in=keys,expire_date__gt=timezone.now()).exists())


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrentLoginLimitTests(TransactionTestCase):
    def test_simultaneous_failures_share_database_counter(self):
        from concurrent.futures import ThreadPoolExecutor
        from django.db import close_old_connections
        from inventory.models import LoginAttempt
        get_user_model().objects.create_user('cuenta-concurrente',password='Solo-Prueba-2026!')
        def attempt(_):
            close_old_connections()
            try:
                result=APIClient().post('/api/auth/login/', {'username':'cuenta-concurrente','password':'incorrecta'},format='json')
                return result.status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=6) as pool:
            statuses=list(pool.map(attempt,range(6)))
        self.assertEqual(sorted(statuses),[400]*5+[429])
        self.assertEqual(LoginAttempt.objects.get().failures,5)
