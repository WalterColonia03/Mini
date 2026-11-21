"""Stage 02: independently exercise field boundaries and session side effects."""
from html.parser import HTMLParser

from django.test import Client, TestCase
from django.urls import reverse

from identity.forms import EmployeeCreationForm, EmployeeEditForm
from identity.models import Account, Role


class _References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.controls = {}
        self.alert_ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
            if attrs.get("role") == "alert":
                self.alert_ids.add(attrs["id"])
        if tag in ("input", "select") and attrs.get("name"):
            self.controls[attrs["name"]] = attrs


class EmployeeFieldAndSessionAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        cls.seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        cls.warehouse_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        cls.password = "FixtureOne7!"
        cls.admin = Account.objects.create_user("admin-fields@example.invalid", cls.password, display_name="Admin Test", role=cls.admin_role)
        cls.seller = Account.objects.create_user("seller-fields@example.invalid", cls.password, display_name="Seller Test", role=cls.seller_role)
        cls.inactive = Account.objects.create_user("inactive-fields@example.invalid", cls.password, display_name="Inactive Test", role=cls.warehouse_role, is_active=False)

    def setUp(self):
        self.client.force_login(self.admin)
        self.create_url = reverse("employee-create")
        self.edit_url = reverse("employee-edit", args=[self.seller.pk])
        self.data = {"display_name": "Nuevo Ejemplo", "email": "new-fields@example.invalid", "role": self.seller_role.pk, "password": self.password}

    def test_create_empty_and_invalid_fields_do_not_create_accounts(self):
        count = Account.objects.count()
        response = self.client.post(self.create_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context["form"].errors), {"display_name", "email", "role", "password"})
        for changes, field in [({"display_name": "   "}, "display_name"), ({"display_name": "A\x00B"}, "display_name"),
                               ({"email": "not-an-email"}, "email"), ({"role": "999999999"}, "role"),
                               ({"role": ""}, "role"), ({"password": "abcdef1"}, "password")]:
            with self.subTest(field=field):
                response = self.client.post(self.create_url, {**self.data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(Account.objects.count(), count)

    def test_name_boundary_trim_and_persistence(self):
        accepted = "A" * 120
        response = self.client.post(self.create_url, {**self.data, "display_name": "  " + accepted + "  "})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Account.objects.get(email_normalized=self.data["email"]).display_name, accepted)
        before = Account.objects.count()
        response = self.client.post(self.create_url, {**self.data, "email": "second-fields@example.invalid", "display_name": "B" * 121})
        self.assertEqual(response.status_code, 200)
        self.assertIn("display_name", response.context["form"].errors)
        self.assertEqual(Account.objects.count(), before)

    def test_email_boundaries_and_normalization_for_create_and_edit(self):
        suffix = "@example.invalid"
        email254 = "a" * (254 - len(suffix)) + suffix
        good = {**self.data, "email": email254}
        self.assertTrue(EmployeeCreationForm(good).is_valid())
        response = self.client.post(self.create_url, good)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Account.objects.filter(email_normalized=email254).exists())
        too_long = "b" + email254
        response = self.client.post(self.create_url, {**self.data, "email": too_long})
        self.assertIn("email", response.context["form"].errors)
        data = {"display_name": self.seller.display_name, "email": "  SELLER-FIELDS@EXAMPLE.INVALID  ", "role": self.seller_role.pk, "new_password": ""}
        response = self.client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.email_normalized, "seller-fields@example.invalid")
        self.assertEqual(self.seller.email, "SELLER-FIELDS@EXAMPLE.INVALID")

    def test_inactive_duplicate_cannot_be_created_or_edited(self):
        count = Account.objects.count()
        response = self.client.post(self.create_url, {**self.data, "email": " INACTIVE-FIELDS@EXAMPLE.INVALID "})
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(Account.objects.count(), count)
        response = self.client.post(self.edit_url, {"display_name": "Keep", "email": self.inactive.email, "role": self.seller_role.pk, "new_password": ""})
        self.assertIn("email", response.context["form"].errors)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.display_name, "Seller Test")
        self.assertEqual(self.seller.email_normalized, "seller-fields@example.invalid")

    def test_edit_invalid_inputs_keep_every_original_value(self):
        original = (self.seller.display_name, self.seller.email, self.seller.role_id, self.seller.password)
        data = {"display_name": self.seller.display_name, "email": self.seller.email, "role": self.seller_role.pk, "new_password": ""}
        for changes, field in [({"display_name": ""}, "display_name"), ({"display_name": "X" * 121}, "display_name"),
                               ({"email": "invalid"}, "email"), ({"role": "-1"}, "role"), ({"new_password": "abc"}, "new_password")]:
            with self.subTest(field=field):
                response = self.client.post(self.edit_url, {**data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.seller.refresh_from_db()
                self.assertEqual((self.seller.display_name, self.seller.email, self.seller.role_id, self.seller.password), original)

    def test_optional_password_preserves_sessions_then_change_invalidates_two(self):
        first, second = Client(), Client()
        first.force_login(self.seller)
        second.force_login(self.seller)
        self.assertEqual(first.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(second.get(reverse("dashboard")).status_code, 200)
        data = {"display_name": self.seller.display_name, "email": self.seller.email, "role": self.seller_role.pk, "new_password": ""}
        old_hash = self.seller.password
        response = self.client.post(self.edit_url, data)
        self.seller.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.seller.password, old_hash)
        self.assertEqual(first.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(second.get(reverse("dashboard")).status_code, 200)
        response = self.client.post(self.edit_url, {**data, "new_password": "FixtureTwo9!"})
        self.assertEqual(response.status_code, 302)
        self.seller.refresh_from_db()
        self.assertNotEqual(self.seller.password, old_hash)
        self.assertTrue(self.seller.check_password("FixtureTwo9!"))
        self.assertEqual(first.get(reverse("dashboard")).status_code, 302)
        self.assertEqual(second.get(reverse("dashboard")).status_code, 302)

    def test_non_admin_post_and_csrf_rejected_without_mutation(self):
        original = (self.seller.display_name, self.seller.email, self.seller.role_id, Account.objects.count())
        for account in [self.seller, self.inactive]:
            if not account.is_active:
                account = Account.objects.create_user("warehouse-fields@example.invalid", self.password, display_name="Warehouse", role=self.warehouse_role)
                original = (self.seller.display_name, self.seller.email, self.seller.role_id, Account.objects.count())
            client = Client()
            client.force_login(account)
            self.assertEqual(client.post(self.create_url, self.data).status_code, 403)
            self.assertEqual(client.post(self.edit_url, {"display_name":"Tampered", "email":self.seller.email, "role":self.admin_role.pk}).status_code, 403)
            self.seller.refresh_from_db()
            self.assertEqual((self.seller.display_name, self.seller.email, self.seller.role_id, Account.objects.count()), original)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.admin)
        self.assertEqual(csrf.post(self.create_url, self.data).status_code, 403)
        self.assertEqual(Account.objects.count(), original[-1])

    def test_form_render_never_refills_password_and_role_choices_are_restricted(self):
        create = EmployeeCreationForm({**self.data, "email": "invalid"})
        self.assertFalse(create.is_valid())
        self.assertNotIn(self.password, str(create["password"]))
        edit = EmployeeEditForm({"display_name":"Name", "email":"invalid", "role":self.seller_role.pk, "new_password":self.password})
        self.assertFalse(edit.is_valid())
        self.assertNotIn(self.password, str(edit["new_password"]))
        self.assertEqual(set(create.fields["role"].queryset.values_list("code", flat=True)), set(Role.Code.values))

    def test_create_and_edit_errors_and_help_have_resolvable_accessible_references(self):
        for url, data, invalid in [
            (self.create_url, {}, {"display_name", "email", "password", "role"}),
            (self.edit_url, {"display_name": "", "email": "invalid", "role": "", "new_password": "abc"},
             {"display_name", "email", "new_password", "role"}),
        ]:
            with self.subTest(url=url):
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 200)
                parser = _References()
                parser.feed(response.content.decode("utf-8"))
                for name in invalid:
                    control = parser.controls[name]
                    self.assertEqual(control.get("aria-invalid"), "true")
                    targets = set(control.get("aria-describedby", "").split())
                    self.assertIn(f"id_{name}_error", targets)
                    self.assertTrue(targets.issubset(parser.ids), (name, targets - parser.ids))
                    self.assertIn(f"id_{name}_error", parser.alert_ids)
