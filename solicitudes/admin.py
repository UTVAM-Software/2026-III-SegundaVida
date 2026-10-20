from django.contrib import admin
from .models import Solicitud


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):

    list_display = (
        "usuario",
        "objeto",
        "estado",
        "fecha_solicitud",
    )

    list_filter = (
        "estado",
        "fecha_solicitud",
    )

    search_fields = (
        "usuario__username",
        "objeto__nombre",
        "mensaje",
    )