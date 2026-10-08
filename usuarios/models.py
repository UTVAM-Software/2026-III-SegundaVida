from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    ubicacion = models.CharField(max_length=200, blank=True)
    biografia = models.TextField(blank=True)

    karma = models.IntegerField(default=0)
    reputacion = models.FloatField(default=5.0)

    def __str__(self):
        return self.usuario.username


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )

    mensaje = models.CharField(max_length=255)

    leida = models.BooleanField(default=False)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.mensaje}"