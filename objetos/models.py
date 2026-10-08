from django.db import models
from django.contrib.auth.models import User


class Objeto(models.Model):

    CATEGORIAS = [
        ("electronica", "Electrónica"),
        ("muebles", "Muebles"),
        ("ropa", "Ropa"),
        ("libros", "Libros"),
        ("juguetes", "Juguetes"),
        ("hogar", "Hogar"),
        ("otros", "Otros"),
    ]

    ACCIONES = [
        ("donar", "Donar"),
        ("intercambiar", "Intercambiar"),
        ("reparar", "Reparar"),
        ("piezas", "Dar para piezas"),
        ("transformar", "Transformar"),
    ]

    ESTADOS = [
        ("nuevo", "Nuevo"),
        ("bueno", "Bueno"),
        ("regular", "Regular"),
        ("danado", "Dañado"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()

    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS
    )

    accion = models.CharField(
        max_length=20,
        choices=ACCIONES
    )

    funciona = models.BooleanField(default=True)

    ubicacion = models.CharField(
        max_length=200,
        blank=True
    )

    latitud = models.FloatField(
    null=True,
    blank=True
    )

    longitud = models.FloatField(
        null=True,
        blank=True
    )

    fecha_publicacion = models.DateTimeField(
        auto_now_add=True
    )

    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class ImagenObjeto(models.Model):

    objeto = models.ForeignKey(
        Objeto,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    imagen = models.ImageField(
        upload_to="objetos/"
    )

    fecha_subida = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Imagen de {self.objeto.nombre}"

class LugarSegundaVida(models.Model):

    TIPOS = [
        ("taller", "Taller"),
        ("centro_acopio", "Centro de acopio"),
        ("organizacion", "Organización"),
        ("negocio", "Negocio"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField(max_length=150)

    descripcion = models.TextField()

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS
    )

    categorias = models.JSONField(default=list)

    servicios = models.TextField()

    ubicacion = models.CharField(max_length=255)

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    horario = models.CharField(
        max_length=255,
        blank=True
    )

    imagen = models.ImageField(
        upload_to="lugares/",
        blank=True,
        null=True
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre