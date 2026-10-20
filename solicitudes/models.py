from django.db import models
from django.contrib.auth.models import User
from objetos.models import Objeto


class Solicitud(models.Model):

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aceptada", "Aceptada"),
        ("rechazada", "Rechazada"),
        ("cumplida", "Cumplida"),
        ("no_cumplida", "No cumplida"),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitudes"
    )

    objeto = models.ForeignKey(
        Objeto,
        on_delete=models.CASCADE,
        related_name="solicitudes"
    )

    mensaje = models.TextField(blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendiente"
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "objeto"],
                condition=models.Q(estado="pendiente"),
                name="solicitud_pendiente_unica_por_usuario_objeto",
            ),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.objeto.nombre}"

class Valoracion(models.Model):

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="valoraciones"
    )   

    valorador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="valoraciones_realizadas"
    )

    valorado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="valoraciones_recibidas"
    )

    puntuacion = models.PositiveSmallIntegerField()

    comentario = models.TextField(blank=True)

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(puntuacion__gte=1) &
                        models.Q(puntuacion__lte=5),
                name="valoracion_puntuacion_entre_1_y_5",
            ),
            models.UniqueConstraint(
                fields=["solicitud", "valorador"],
                name="una_valoracion_por_usuario_solicitud",
            ),
        ]

    def __str__(self):
        return (
            f"{self.valorador.username} → "
            f"{self.valorado.username} ({self.puntuacion}/5)"
        )