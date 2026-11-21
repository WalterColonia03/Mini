from django import forms

from .models import Role


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo de trabajo",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "nombre@empresa.com",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Ingrese su contraseña",
            }
        ),
    )


# ── HU-USR-02 · Formulario de creación de empleado ───────────────────────────

class RoleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Role) -> str:
        return obj.name


def _validate_strong_password(value: str) -> str:
    if len(value) < 7:
        raise forms.ValidationError(
            "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."
        )
    has_upper = any(ch.isupper() for ch in value)
    has_lower = any(ch.islower() for ch in value)
    has_digit = any(ch.isdigit() for ch in value)
    if not (has_upper and has_lower and has_digit):
        raise forms.ValidationError(
            "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."
        )
    if len(set(value)) == 1 or value.lower() in {
        "1234567",
        "12345678",
        "123456789",
        "password",
        "contraseña",
        "qwertyui",
    }:
        raise forms.ValidationError(
            "La contraseña elegida es demasiado débil o predecible. Combine letras y números distintos."
        )
    return value


class EmployeeCreationForm(forms.Form):
    display_name = forms.CharField(
        label="Nombre completo",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej.: Ana García"}),
    )
    email = forms.EmailField(
        label="Correo de trabajo",
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "ana@empresa.com"}),
    )
    password = forms.CharField(
        label="Contraseña inicial",
        strip=False,
        min_length=7,
        help_text="Mínimo 7 caracteres, con al menos una mayúscula, una minúscula y un número.",
        error_messages={
            "min_length": "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.",
            "required": "Ingrese una contraseña inicial.",
        },
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    role = RoleChoiceField(
        label="Rol",
        queryset=Role.objects.filter(code__in=Role.Code.values),
        empty_label="— Seleccionar rol —",
        error_messages={
            "invalid_choice": "Seleccione un rol válido de la lista.",
            "required": "Seleccione un rol para el empleado.",
        },
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_password(self) -> str:
        return _validate_strong_password(self.cleaned_data["password"])


# ── HU-USR-03 · Formulario de edición de empleado ────────────────────────────

class EmployeeEditForm(forms.Form):
    display_name = forms.CharField(
        label="Nombre completo",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Correo de trabajo",
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    role = RoleChoiceField(
        label="Rol",
        queryset=Role.objects.filter(code__in=Role.Code.values),
        empty_label="— Seleccionar rol —",
        error_messages={
            "invalid_choice": "Seleccione un rol válido de la lista.",
            "required": "Seleccione un rol para el empleado.",
        },
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    new_password = forms.CharField(
        label="Nueva contraseña (opcional)",
        required=False,
        strip=False,
        min_length=7,
        help_text="Déjelo en blanco si no desea cambiar la contraseña actual. Si ingresa una nueva, debe tener al menos 7 caracteres, mayúscula, minúscula y número.",
        error_messages={
            "min_length": "La nueva contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.",
        },
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def clean_new_password(self) -> str:
        value = self.cleaned_data.get("new_password") or ""
        if not value:
            return ""
        return _validate_strong_password(value)
