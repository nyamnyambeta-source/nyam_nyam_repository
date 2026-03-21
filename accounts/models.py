from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    PROFILE_OPTIONS = (
        ('admin', 'Admin'),
        ('manager', 'Encargado'),
        ('worker', 'Trabajador')
    )

    USER_PERMISSIONS = (
        ('admin', 'Poder absoluto'),
        ('crud', 'Crear, actualizar y eliminar'), 
        ('observer', 'Solo observar')
    )

    role = models.CharField(max_length=15, choices=PROFILE_OPTIONS, default='worker')
    permission = models.CharField(max_length=50, choices=USER_PERMISSIONS, default='crud')

