
from django.db import migrations


def cargar_categorias(apps, schema_editor):
    Categoria = apps.get_model("objetos", "Categoria")

    categorias = [
        ("electronica", "Electrónica"),
        ("muebles", "Muebles"),
        ("ropa", "Ropa"),
        ("libros", "Libros"),
        ("juguetes", "Juguetes"),
        ("hogar", "Hogar"),
        ("otros", "Otros"),
    ]

    for nombre, descripcion in categorias:
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={
                "descripcion": descripcion,
                "activa": True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ("objetos", "0005_categoria_alter_objeto_categoria"),
    ]

    operations = [
        migrations.RunPython(
            cargar_categorias,
            migrations.RunPython.noop
        ),
    ]
