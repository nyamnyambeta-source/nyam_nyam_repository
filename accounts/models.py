from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    PROFILE_OPTIONS = (
        ('admin', 'Admin'),
        ('encargado', 'Encargado'),
        ('trabajador', 'Trabajador')
    )

    user_permissions = (
        ('admin', 'Poder absoluto'),
        ('CRUD', 'Crear, actualizar y eliminar'), 
        ('Observer', 'Solo observar')
    )

    role = models.CharField(max_length=15, choices=PROFILE_OPTIONS, default='admin')
    permision = models.CharField(max_length=10, choices=user_permissions, default='CRUD')