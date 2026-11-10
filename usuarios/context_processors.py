from .models import Notificacion


def notificaciones_no_leidas(request):

    if request.user.is_authenticated:

        notificaciones = Notificacion.objects.filter(
            usuario=request.user
        ).order_by("-fecha")

        no_leidas = notificaciones.filter(
            leida=False
        ).count()

    else:

        notificaciones = Notificacion.objects.none()
        no_leidas = 0

    return {
        "notificaciones": notificaciones,
        "notificaciones_no_leidas": no_leidas,
    }
