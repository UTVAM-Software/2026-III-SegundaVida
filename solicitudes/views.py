from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from objetos.models import Objeto
from .models import Solicitud, Valoracion
from .forms import SolicitudForm, ValoracionForm
from usuarios.models import Notificacion


def crear_notificacion(usuario, mensaje):
    return Notificacion.objects.create(
        usuario=usuario,
        mensaje=mensaje
    )

@login_required
def solicitar_objeto(request, id):

    objeto = get_object_or_404(
        Objeto,
        id=id
    )

    if objeto.usuario == request.user:
        messages.error(
            request,
            "No puedes solicitar tu propio objeto."
        )
        return redirect("detalle_objeto", id=objeto.id)

    if not objeto.disponible:
        messages.warning(
            request,
            "Este objeto ya no está disponible."
        )
        return redirect("detalle_objeto", id=objeto.id)

    solicitud_existente = Solicitud.objects.filter(
        usuario=request.user,
        objeto=objeto,
        estado="pendiente"
    ).exists()

    if solicitud_existente:
        messages.warning(
            request,
            "Ya tienes una solicitud pendiente para este objeto."
        )
        return redirect("detalle_objeto", id=objeto.id)

    if request.method == "POST":

        formulario = SolicitudForm(request.POST)

        if formulario.is_valid():

            solicitud = formulario.save(commit=False)

            solicitud.usuario = request.user
            solicitud.objeto = objeto
            solicitud.estado = "pendiente"

            solicitud.save()

            crear_notificacion(
                objeto.usuario,
                f'El usuario "{request.user.username}" ha solicitado tu objeto "{objeto.nombre}".'
            )

            perfil = request.user.perfil
            perfil.karma += 1
            perfil.save(update_fields=["karma"])

            messages.success(
                request,
                "¡Solicitud enviada correctamente!"
            )

            return redirect(
                "detalle_objeto",
                id=objeto.id
            )

    else:
        formulario = SolicitudForm()

    return render(
        request,
        "solicitudes/solicitar.html",
        {
            "formulario": formulario,
            "objeto": objeto,
        }
    )

@login_required
def solicitudes_recibidas(request):

    valoraciones_usuario = Valoracion.objects.filter(
        valorador=request.user
    )

    solicitudes = Solicitud.objects.filter(
        objeto__usuario=request.user
    ).select_related(
        "usuario",
        "objeto"
    ).prefetch_related(
        Prefetch(
            "valoraciones",
            queryset=valoraciones_usuario,
            to_attr="valoraciones_del_usuario"
        )
    ).order_by("-fecha_solicitud")

    return render(
        request,
        "solicitudes/recibidas.html",
        {"solicitudes": solicitudes}
    )

@login_required
def responder_solicitud(request, id, accion):
    if request.method != "POST":
        messages.warning(
            request,
            "Esta acción debe realizarse mediante el formulario."
        )
        return redirect("solicitudes_recibidas")

    if accion not in ["aceptar", "rechazar"]:
        messages.error(request, "La acción solicitada no es válida.")
        return redirect("solicitudes_recibidas")

    with transaction.atomic():
        solicitud = get_object_or_404(
            Solicitud.objects.select_for_update(),
            id=id
        )

        if solicitud.objeto.usuario != request.user:
            messages.error(
                request,
                "No tienes permiso para responder esta solicitud."
            )
            return redirect("solicitudes_recibidas")

        if solicitud.estado != "pendiente":
            messages.warning(
                request,
                "Esta solicitud ya no está pendiente."
            )
            return redirect("solicitudes_recibidas")

        objeto = solicitud.objeto

        if accion == "rechazar":
            solicitud.estado = "rechazada"
            solicitud.save(update_fields=["estado"])

            crear_notificacion(
                solicitud.usuario,
                f'Tu solicitud para el objeto "{objeto.nombre}" ha sido rechazada.'
            )

            messages.success(
                request,
                "Solicitud rechazada correctamente."
            )

        else:  # accion == "aceptar"
            objeto = Objeto.objects.select_for_update().get(
                id=objeto.id
            )

            if not objeto.disponible:
                messages.warning(
                    request,
                    "Este objeto ya no está disponible."
                )
                return redirect("solicitudes_recibidas")

            solicitud.estado = "aceptada"
            solicitud.save(update_fields=["estado"])

            objeto.disponible = False
            objeto.save(update_fields=["disponible"])

            crear_notificacion(
                solicitud.usuario,
                f'Tu solicitud para el objeto "{objeto.nombre}" ha sido aceptada.'
            )

            perfil = request.user.perfil
            perfil.karma += 2
            perfil.save(update_fields=["karma"])

            solicitudes_rechazadas = Solicitud.objects.select_for_update().filter(
                objeto=objeto,
                estado="pendiente"
            ).exclude(id=solicitud.id)

            for solicitud_rechazada in solicitudes_rechazadas:
                solicitud_rechazada.estado = "rechazada"
                solicitud_rechazada.save(update_fields=["estado"])

                crear_notificacion(
                    solicitud_rechazada.usuario,
                    f'Tu solicitud para el objeto "{objeto.nombre}" ha sido rechazada porque otra solicitud fue aceptada.'
                )

            messages.success(
                request,
                "¡Solicitud aceptada! El objeto ahora no está disponible."
            )

    return redirect("solicitudes_recibidas")

@login_required
def mis_solicitudes(request):

    valoraciones_usuario = Valoracion.objects.filter(
        valorador=request.user
    )

    solicitudes = Solicitud.objects.filter(
        usuario=request.user
    ).select_related(
        "objeto",
        "objeto__usuario"
    ).prefetch_related(
        Prefetch(
            "valoraciones",
            queryset=valoraciones_usuario,
            to_attr="valoraciones_del_usuario"
        )
    ).order_by("-fecha_solicitud")

    return render(
        request,
        "solicitudes/mis_solicitudes.html",
        {"solicitudes": solicitudes}
    )

@login_required
def marcar_solicitud(request, id, estado):

    if request.method != "POST":
        messages.warning(
            request,
            "Esta acción debe realizarse mediante el formulario."
        )
        return redirect("mis_solicitudes")

    solicitud = get_object_or_404(
        Solicitud,
        id=id
    )

    if solicitud.usuario != request.user:
        messages.error(
            request,
            "No tienes permiso para modificar esta solicitud."
        )
        return redirect("mis_solicitudes")

    if solicitud.estado != "aceptada":
        messages.warning(
            request,
            "Solo una solicitud aceptada puede marcarse como cumplida o no cumplida."
        )
        return redirect("mis_solicitudes")

    if estado == "cumplida":
        solicitud.estado = "cumplida"

        perfil = request.user.perfil
        perfil.karma += 3
        perfil.save(update_fields=["karma"])

        crear_notificacion(
            solicitud.objeto.usuario,
            f'La solicitud para tu objeto "{solicitud.objeto.nombre}" ha sido marcada como cumplida.'
        )

        messages.success(
            request,
            "¡Acuerdo marcado como cumplido!"
        )

    elif estado == "no_cumplida":

        solicitud.estado = "no_cumplida"

        solicitud.objeto.disponible = True
        solicitud.objeto.save(
            update_fields=["disponible"]
        )

        messages.warning(
            request,
            "El acuerdo fue marcado como no cumplido. "
            "El objeto vuelve a estar disponible."
        )

    else:
        messages.error(
            request,
            "El estado solicitado no es válido."
        )
        return redirect("mis_solicitudes")

    solicitud.save()

    return redirect("mis_solicitudes")

@login_required
def valorar_solicitud(request, id):

    solicitud = get_object_or_404(
        Solicitud,
        id=id
    )

 
    if solicitud.estado not in ["cumplida", "no_cumplida"]:
        messages.warning(
            request,
            "Solo puedes valorar una interacción cumplida o no cumplida."
        )
        return redirect("mis_solicitudes")

    
    propietario = solicitud.objeto.usuario
    solicitante = solicitud.usuario

    if request.user not in [propietario, solicitante]:
        messages.error(
            request,
            "No participaste en esta interacción."
        )
        return redirect("mis_solicitudes")

   
    if propietario == solicitante:
        messages.error(
            request,
            "No puedes valorar tu propia cuenta."
        )
        return redirect("mis_solicitudes")

    
    if Valoracion.objects.filter(
        solicitud=solicitud,
        valorador=request.user
    ).exists():

        messages.warning(
            request,
            "Ya has valorado esta interacción."
        )
        return redirect("mis_solicitudes")

    if request.user == solicitante:
        usuario_valorado = propietario
    else:
        usuario_valorado = solicitante

    if request.method == "POST":

        formulario = ValoracionForm(request.POST)

        if formulario.is_valid():

            valoracion = formulario.save(commit=False)

            valoracion.solicitud = solicitud
            valoracion.valorador = request.user
            valoracion.valorado = usuario_valorado

            valoracion.save()

            perfil = request.user.perfil
            perfil.karma += 1
            perfil.save(update_fields=["karma"])

            valoraciones_recibidas = Valoracion.objects.filter(
                valorado=usuario_valorado
            )

            promedio = valoraciones_recibidas.aggregate(
                promedio=models.Avg("puntuacion")
            )["promedio"]

            usuario_valorado.perfil.reputacion = round(promedio, 2)
            usuario_valorado.perfil.save()

            messages.success(
                request,
                "¡Valoración registrada correctamente!"
            )

            return redirect("mis_solicitudes")

    else:
        formulario = ValoracionForm()

    return render(
        request,
        "solicitudes/valorar.html",
        {
            "formulario": formulario,
            "solicitud": solicitud,
            "usuario_valorado": usuario_valorado,
        }
    )

