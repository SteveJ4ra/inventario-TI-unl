from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from .test_store import RetirementStoreTests
from .test_models import RetirementFixtures
from inventory.retirement_models import ReviewerProfile, DecommissionRequest


class RetirementApiTests(RetirementFixtures):
    def setUp(self):
        super().setUp()
        self.requester.groups.add(Group.objects.create(name="Gestores"))
        self.reviewer.groups.add(Group.objects.create(name="Revisores"))
        self.client=APIClient()
    def test_anonymous_and_manager_cannot_access_reviewer_admin(self):
        self.assertEqual(self.client.get("/api/operator/reviewers/").status_code,403)
        self.client.force_login(self.requester)
        self.assertEqual(self.client.get("/api/operator/reviewers/").status_code,403)
    def test_temporary_reviewer_denied_until_password_change(self):
        self.reviewer.set_password("Old-Fixture-42!");self.reviewer.save()
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get("/api/reviewer/retirement-requests/").status_code,403)
        response=self.client.post("/api/auth/change-password/",{"current_password":"Old-Fixture-42!","new_password":"New-Fixture-Secure-785!"},format="json")
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.client.get("/api/reviewer/retirement-requests/").status_code,200)
    def test_manager_requests_and_assigned_reviewer_decides(self):
        self.client.force_login(self.requester)
        response=self.client.post(f"/api/assets/{self.asset.pk}/retirement-requests/",{"reason":"Pérdida","reviewer_id":self.reviewer.pk,"expected_revision":0},format="json")
        self.assertEqual(response.status_code,201,response.content)
        request_id=response.json()["id"]
        profile=self.reviewer.reviewer_profile;profile.must_change_password=False;profile.save()
        self.client.force_login(self.reviewer)
        response=self.client.post(f"/api/retirement-requests/{request_id}/decision/",{"decision":"approve","expected_revision":1},format="json")
        self.assertEqual(response.status_code,201,response.content)
        self.asset.refresh_from_db();self.assertEqual(self.asset.lifecycle_status,"baja")
    def test_other_reviewer_cannot_read_or_decide_request(self):
        record=self.create_request()
        other=get_user_model().objects.create(username="other")
        other.groups.add(Group.objects.get(name="Revisores"))
        ReviewerProfile.objects.create(user=other,faculty=self.other,must_change_password=False)
        self.client.force_login(other)
        self.assertEqual(self.client.get("/api/reviewer/retirement-requests/").json(),[])
        self.assertEqual(self.client.post(f"/api/retirement-requests/{record.pk}/decision/",{"decision":"approve","expected_revision":0},format="json").status_code,404)

    def test_session_methods_and_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        self.requester.set_password("Manager-Fixture-42!");self.requester.save()
        credentials={"username":self.requester.username,"password":"Manager-Fixture-42!"}
        self.assertEqual(client.post("/api/auth/login/",credentials,format="json").status_code,403)
        token=client.get("/api/auth/csrf/").json()["csrfToken"]
        response=client.post("/api/auth/login/",credentials,format="json",HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(client.post("/api/auth/me/",{},format="json").status_code,403)
        token=client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.post("/api/auth/me/",{},format="json",HTTP_X_CSRFTOKEN=token).status_code,405)
        self.assertEqual(client.get("/api/auth/logout/").status_code,405)
        self.assertEqual(client.post("/api/auth/logout/",{},format="json",HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(client.get("/api/auth/me/").status_code,403)

    def test_operator_can_create_reviewer_but_cannot_deactivate_pending(self):
        operator=get_user_model().objects.create_user(username="operator")
        operator.groups.add(Group.objects.create(name="Operadores"))
        self.client.force_login(operator)
        response=self.client.post("/api/operator/reviewers/",{"username":"new-reviewer","faculty_id":self.other.pk,"password":"Secure-Unique-Fixture-785!"},format="json")
        self.assertEqual(response.status_code,201,response.content)
        self.assertNotIn("password",response.json())
        record=self.create_request()
        self.assertEqual(self.client.patch(f"/api/operator/reviewers/{self.reviewer.id}/",{"active":False},format="json").status_code,409)
        self.reviewer.refresh_from_db();self.assertTrue(self.reviewer.is_active)
        response=self.client.post(f"/api/retirement-requests/{record.pk}/reassign/",{"reviewer_id":response.json()["id"],"expected_revision":0},format="json")
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.client.patch(f"/api/operator/reviewers/{self.reviewer.id}/",{"active":False},format="json").status_code,200)

    def test_initial_password_change_cannot_reuse_password_or_use_weak_one(self):
        self.reviewer.set_password("Old-Fixture-42!");self.reviewer.save()
        self.client.force_login(self.reviewer)
        for data in ({"current_password":"wrong","new_password":"Strong-Another-42!"},{"current_password":"Old-Fixture-42!","new_password":"Old-Fixture-42!"},{"current_password":"Old-Fixture-42!","new_password":"123"}):
            with self.subTest(data_keys=list(data)):
                self.assertEqual(self.client.post("/api/auth/change-password/",data,format="json").status_code,400)
        self.assertTrue(ReviewerProfile.objects.get(user=self.reviewer).must_change_password)
