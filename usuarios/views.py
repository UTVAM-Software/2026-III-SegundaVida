from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect, render, get_object_or_404

from .forms import RegistroForm, PerfilForm
from .models import Perfil, Notificacion
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

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

            Perfil.objects.create(
                usuario=usuario,
                nombre=usuario.username
            )

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



from django.http import HttpResponseForbidden


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
        nuevo_rol = request.POST.get("rol")

        if nuevo_rol not in roles:
            messages.error(request, "El rol seleccionado no es válido.")
            return redirect("administrar_usuarios")

        usuario = get_object_or_404(User, username=username)

        if usuario.is_superuser or usuario == request.user:
            messages.error(
                request,
                "No puedes modificar el rol de una cuenta administradora."
            )
            return redirect("administrar_usuarios")

        grupo = Group.objects.get(name=nuevo_rol)
        usuario.groups.set([grupo])

        messages.success(
            request,
            f"El rol de {usuario.username} se actualizó correctamente."
        )

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
