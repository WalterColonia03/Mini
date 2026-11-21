from django.test import Client
from django.urls import reverse
from django.template.loader import render_to_string
from django.test import RequestFactory
from identity.test_audit02e_contracts import Sublot02EContractsTests
from identity.forms import EmployeeCreationForm
class Edges(Sublot02EContractsTests):
    def test_last_admin_and_empty_render(self):
        self.admin2.is_active=False
        self.admin2.save(update_fields=["is_active"])
        self.client.force_login(self.admin)
        url=reverse("employee-state-confirm",args=[self.admin.pk])
        response=self.client.get(url)
        self.assertContains(response,"Es el último administrador activo; el sistema rechazará dejar cero administradores activos.")
        self.assertContains(response,"La cuenta seguirá activa y conservará sus sesiones.")
        req=RequestFactory().get("/empleados/")
        req.user=self.admin
        html=render_to_string("identity/employee_list.html",{"accounts":[],"query":""},request=req)
        self.assertIn("No hay empleados registrados.",html)
    def test_defensive_messages_at_http_boundary(self):
        self.client.force_login(self.admin)
        for name, post, field, expected in [
            ("employee-create",{"role":"99999999"},"role","Seleccione un rol válido de la lista."),
            ("employee-create",{"password":"password"},"password","La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."),
            ("employee-create",{},"email","Este campo es obligatorio."),
        ]:
            with self.subTest(field=field):
                response=self.client.post(reverse(name),post)
                self.assertEqual(response.context["form"].errors[field],[expected])
        self.admin2.is_active=False
        self.admin2.save(update_fields=["is_active"])
        edit=self.client.post(reverse("employee-edit",args=[self.admin.pk]),{
            "display_name":self.admin.display_name, "email":self.admin.email,"role":self.seller_role.pk})
        self.assertContains(edit,"No puedes cambiar el rol de tu propia cuenta.")
        state=self.client.post(reverse("employee-deactivate",args=[self.admin.pk]),{"action":"desactivar"},follow=True)
        self.assertContains(state,"No puedes desactivar tu propia cuenta.")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
