
from solicitudes.models import Solicitud


PESO_REFERENCIA_POR_CATEGORIA = {
    "electronica": 1.5,
    "muebles": 25.0,
    "ropa": 0.5,
    "libros": 0.4,
    "juguetes": 0.3,
    "hogar": 2.0,
    "otros": 1.0,
}


def calcular_material_reutilizado_estimado(objeto):
    categoria = objeto.categoria.nombre.lower()

    return PESO_REFERENCIA_POR_CATEGORIA.get(
        categoria,
        1.0
    )


def calcular_material_reutilizado_comunidad():
    solicitudes_cumplidas = Solicitud.objects.filter(
        estado="cumplida"
    ).select_related("objeto", "objeto__categoria")

    total = 0

    for solicitud in solicitudes_cumplidas:
        total += calcular_material_reutilizado_estimado(
            solicitud.objeto
        )

    return total


def calcular_material_reutilizado_por_categoria():
    solicitudes_cumplidas = Solicitud.objects.filter(
        estado="cumplida"
    ).select_related("objeto", "objeto__categoria")

    impacto = {}

    for solicitud in solicitudes_cumplidas:
        categoria = solicitud.objeto.categoria.nombre
        material = calcular_material_reutilizado_estimado(
            solicitud.objeto
        )

        impacto[categoria] = (
            impacto.get(categoria, 0) + material
        )

    return impacto
