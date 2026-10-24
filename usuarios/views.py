from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404

from .forms import RegistroForm, PerfilForm
from .models import Perfil, Notificacion
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


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

@login_required
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

