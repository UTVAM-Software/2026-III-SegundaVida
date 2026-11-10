from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def roles_permitidos(*roles):

    def decorador(vista):

        @login_required
        @wraps(vista)
        def vista_protegida(request, *args, **kwargs):

            usuario = request.user

            # El superusuario tiene acceso total
            if usuario.is_superuser:
                return vista(request, *args, **kwargs)

            grupos = set(
                usuario.groups.values_list("name", flat=True)
            )

            # Solo lectura nunca puede ejecutar operaciones de usuario
            if "Solo lectura" in grupos and "Usuario" in roles:
                messages.error(
                    request,
                    "Tu cuenta tiene permisos de solo lectura."
                )
                return redirect("inicio")

            if any(rol in grupos for rol in roles):
                return vista(request, *args, **kwargs)

            messages.error(
                request,
                "No tienes permisos para realizar esta acción."
            )

            return redirect("inicio")

        return vista_protegida

    return decorador