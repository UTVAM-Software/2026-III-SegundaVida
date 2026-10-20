from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from objetos.views import (
    inicio,
    publicar_objeto,
    lista_objetos,
    detalle_objeto,
    editar_objeto,
    eliminar_objeto,
    mis_objetos,
    lugares_segunda_vida,
    detalle_lugar,
)

from solicitudes.views import (
    solicitar_objeto,
    solicitudes_recibidas,
    responder_solicitud,
    mis_solicitudes,
    marcar_solicitud,
    valorar_solicitud,
)

from usuarios.views import (
    registro,
    perfil,
    editar_perfil,
    perfil_publico,
    notificaciones,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("django.contrib.auth.urls")),

    # Usuarios
    path("registro/", registro, name="registro"),
    path("perfil/", perfil, name="perfil"),
    path("perfil/editar/", editar_perfil, name="editar_perfil"),
    path("perfil/<str:username>/", perfil_publico, name="perfil_publico"),
    path("notificaciones/", notificaciones, name="notificaciones"),

    # Inicio y objetos
    path("", inicio, name="inicio"),
    path("publicar/", publicar_objeto, name="publicar_objeto"),
    path("objetos/", lista_objetos, name="lista_objetos"),
    path("objetos/<int:id>/", detalle_objeto, name="detalle_objeto"),
    path("objetos/<int:id>/editar/", editar_objeto, name="editar_objeto"),
    path("objetos/<int:id>/eliminar/", eliminar_objeto, name="eliminar_objeto"),
    path("mis-objetos/", mis_objetos, name="mis_objetos"),

    # Lugares de segunda vida
    path("lugares/", lugares_segunda_vida, name="lugares_segunda_vida"),
    path("lugares/<int:lugar_id>/", detalle_lugar, name="detalle_lugar"),

    # Solicitudes
    path("objetos/<int:id>/solicitar/", solicitar_objeto, name="solicitar_objeto"),
    path("solicitudes/recibidas/", solicitudes_recibidas, name="solicitudes_recibidas"),
    path("solicitudes/mis-solicitudes/", mis_solicitudes, name="mis_solicitudes"),
    path(
        "solicitudes/<int:id>/aceptar/",
        responder_solicitud,
        {"accion": "aceptar"},
        name="aceptar_solicitud",
    ),
    path(
        "solicitudes/<int:id>/rechazar/",
        responder_solicitud,
        {"accion": "rechazar"},
        name="rechazar_solicitud",
    ),
    path(
        "solicitudes/<int:id>/marcar/<str:estado>/",
        marcar_solicitud,
        name="marcar_solicitud",
    ),
    path("solicitudes/<int:id>/valorar/", valorar_solicitud, name="valorar_solicitud"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
