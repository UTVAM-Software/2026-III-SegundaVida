from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User, Group
from django.contrib.sessions.models import Session
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from .forms import RegistroForm, PerfilForm
from .models import Perfil, Notificacion
from django.contrib.auth.decorators import login_required

from .permissions import roles_permitidos


@login_required
def perfil(request):

    perfil_usuario = Perfil.objects.get(
    usuario=request.user
)

    return render(
        request,
        "usuarios/perfil.html",
        {
            "perfil": perfil_usuario
        }
    )

def perfil_publico(request, username):

    usuario = get_object_or_404(
        User,
        username=username
    )

    perfil_usuario = get_object_or_404(
        Perfil,
        usuario=usuario
    )

    return render(
        request,
        "usuarios/perfil_publico.html",
        {
            "perfil": perfil_usuario
        }
    )

@roles_permitidos("Usuario")
def editar_perfil(request):

    perfil_usuario = Perfil.objects.get(
        usuario=request.user
    )

    if request.method == "POST":

        formulario = PerfilForm(
            request.POST,
            instance=perfil_usuario
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "¡Tu perfil se actualizó correctamente!"
            )

            return redirect("perfil")

    else:

        formulario = PerfilForm(
            instance=perfil_usuario
        )

    return render(
        request,
        "usuarios/editar_perfil.html",
        {
            "formulario": formulario
        }
    )

def registro(request):

    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":

        formulario = RegistroForm(request.POST)

        if formulario.is_valid():

            usuario = formulario.save(commit=False)

            usuario.set_password(
                formulario.cleaned_data["password"]
            )

            usuario.save()

            grupo_usuario, _ = Group.objects.get_or_create(
                name="Usuario"
            )
            usuario.groups.add(grupo_usuario)

            login(request, usuario)

            messages.success(
                request,
                "¡Cuenta creada correctamente! Bienvenida a Segunda Vida."
            )

            return redirect("inicio")

    else:
        formulario = RegistroForm()

    return render(
        request,
        "registration/registro.html",
        {
            "formulario": formulario
        }
    )

@login_required
def notificaciones(request):

    if request.method == "POST":

        Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).update(
            leida=True
        )

        return JsonResponse({
            "ok": True,
            "no_leidas": 0,
        })

    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).order_by("-fecha")

    return render(
        request,
        "usuarios/notificaciones.html",
        {
            "notificaciones": notificaciones,
            "no_leidas": notificaciones.filter(
                leida=False
            ).count(),
        }
    )

def administrar_usuarios(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "No tienes permiso para acceder a esta sección."
        )

    roles = ["Usuario", "Solo lectura"]

    if request.method == "POST":

        username = request.POST.get("username")
        accion = request.POST.get("accion")
        usuario = get_object_or_404(User, username=username)

        if usuario.is_superuser or usuario.pk == request.user.pk:
            messages.error(
                request,
                "No puedes modificar ni desactivar esta cuenta."
            )
            return redirect("administrar_usuarios")

        if accion == "cambiar_rol":
            nuevo_rol = request.POST.get("rol")
            if nuevo_rol not in roles:
                messages.error(
                    request,
                    "El rol seleccionado no es válido."
                )
                return redirect("administrar_usuarios")

            grupo, _ = Group.objects.get_or_create(name=nuevo_rol)
            usuario.groups.set([grupo])
            messages.success(
                request,
                f"El rol de {usuario.username} se actualizó correctamente."
            )

        elif accion == "desactivar":
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])

            claves_sesion = []
            sesiones_activas = Session.objects.filter(
                expire_date__gt=timezone.now()
            )
            for sesion in sesiones_activas.iterator():
                if sesion.get_decoded().get("_auth_user_id") == str(usuario.pk):
                    claves_sesion.append(sesion.session_key)

            if claves_sesion:
                Session.objects.filter(
                    session_key__in=claves_sesion
                ).delete()

            messages.success(
                request,
                f"La cuenta de {usuario.username} fue desactivada."
            )

        elif accion == "reactivar":
            usuario.is_active = True
            usuario.save(update_fields=["is_active"])
            messages.success(
                request,
                f"La cuenta de {usuario.username} fue reactivada."
            )

        else:
            messages.error(request, "La acción seleccionada no es válida.")

        return redirect("administrar_usuarios")

    usuarios = []

    for usuario in User.objects.all().order_by("username"):

        if usuario.is_superuser:
            rol = "Super usuario"
        else:
            grupos = list(
                usuario.groups.values_list("name", flat=True)
            )
            rol = grupos[0] if grupos else "Sin rol"

        usuarios.append({
            "usuario": usuario,
            "rol": rol,
        })

    return render(
        request,
        "usuarios/administrar_usuarios.html",
        {
            "usuarios": usuarios,
            "roles": roles,
        }
    )
