from django.contrib import admin
from .models import Objeto, LugarSegundaVida

admin.site.register(LugarSegundaVida)

@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "usuario",
        "categoria",
        "estado",
        "accion",
        "funciona",
        "disponible",
    )

    list_filter = (
        "categoria",
        "estado",
        "accion",
        "funciona",
        "disponible",
    )

    search_fields = (
        "nombre",
        "descripcion",
        "usuario__username",
    )