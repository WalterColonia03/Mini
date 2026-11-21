"""Exact login literals and the accepted 254-character identifier boundary."""
from django.test import SimpleTestCase

from .forms import LoginForm


class LoginLiteralTests(SimpleTestCase):
    def test_email_254_is_valid_and_255_explains_inclusive_maximum(self):
        for length in (254, 255):
            with self.subTest(length=length):
                email = "a" * (length - len("@example.invalid")) + "@example.invalid"
                self.assertEqual(len(email), length)
                form = LoginForm({"email": email, "password": "fictional"})
                self.assertEqual(form.is_valid(), length == 254)
                if length == 255:
                    self.assertEqual(list(form.errors["email"]), [
                        "Asegúrese de que este valor tenga como máximo 254 caracteres (tiene 255)."
                    ])

    def test_required_and_invalid_email_literals(self):
        required = LoginForm({})
        self.assertFalse(required.is_valid())
        self.assertEqual(list(required.errors["email"]), ["Este campo es obligatorio."])
        self.assertEqual(list(required.errors["password"]), ["Este campo es obligatorio."])
        invalid = LoginForm({"email": "sin-arroba", "password": "fictional"})
        self.assertFalse(invalid.is_valid())
        self.assertEqual(list(invalid.errors["email"]), [
            "Introduzca una dirección de correo electrónico válida."
        ])

    def test_null_character_literals_without_echoing_input(self):
        email = LoginForm({"email": "a\x00@example.invalid", "password": "fictional"})
        self.assertFalse(email.is_valid())
        self.assertEqual(list(email.errors["email"]), [
            "Introduzca una dirección de correo electrónico válida.",
            "Los caracteres nulos no están permitidos.",
        ])
        password = LoginForm({"email": "a@example.invalid", "password": "fictional\x00"})
        self.assertFalse(password.is_valid())
        self.assertEqual(list(password.errors["password"]), ["Los caracteres nulos no están permitidos."])

    def test_email_outer_spaces_are_trimmed_before_length_validation(self):
        email = "a" * (254 - len("@example.invalid")) + "@example.invalid"
        form = LoginForm({"email": "  " + email + "  ", "password": "fictional"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], email)
