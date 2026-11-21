from __future__ import annotations

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import validate_email
from django.db import models


class Role(models.Model):
    class Code(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        WAREHOUSE = "ALMACENERO", "Almacenero"
        SELLER = "VENDEDOR", "Vendedor"

    code = models.CharField(max_length=12, unique=True, choices=Code.choices)
    name = models.CharField(max_length=40)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class LoginAttempt(models.Model):
    """Temporary throttle state shared across browser sessions and workers."""

    identifier = models.CharField(max_length=64, primary_key=True)
    failures = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class AccountManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "Account":
        if not email:
            raise ValueError("El correo es obligatorio.")
        if "display_name" in extra_fields and isinstance(extra_fields["display_name"], str):
            extra_fields["display_name"] = extra_fields["display_name"].strip()
        normalized = Account.normalize_email(email)
        account = self.model(email=email.strip(), email_normalized=normalized, **extra_fields)
        if password is None:
            account.set_unusable_password()
        else:
            account.set_password(password)
        account.full_clean()
        account.save(using=self._db)
        return account

    def create_superuser(self, email: str, password: str, **extra_fields: object) -> "Account":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254, unique=True)
    email_normalized = models.CharField(max_length=254, unique=True, editable=False)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="accounts")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name", "role"]

    class Meta:
        ordering = ["email_normalized"]

    @staticmethod
    def normalize_email(value: str) -> str:
        return value.strip().casefold()

    def clean(self) -> None:
        super().clean()
        if isinstance(self.display_name, str):
            self.display_name = self.display_name.strip()
        validate_email(self.email)
        self.email = self.email.strip()
        self.email_normalized = self.normalize_email(self.email)

    def __str__(self) -> str:
        return self.email
