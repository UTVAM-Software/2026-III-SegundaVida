from django.shortcuts import render, redirect, get_object_or_404
from django.db import models, transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from .forms import ObjetoForm, ImagenObjetoForm
from .models import Objeto, Categoria, ImagenObjeto, LugarSegundaVida
from .utils import (
    calcular_material_reutilizado_estimado,
    calcular_material_reutilizado_comunidad,
    calcular_material_reutilizado_por_categoria,
)

def geocodificar_ubicacion(ubicacion):
    """
    Convierte una ubicación escrita en texto
    a latitud y longitud usando OpenStreetMap Nominatim.
    """

    if not ubicacion:
        return None, None

    consulta = quote(ubicacion)

    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={consulta}&format=json&limit=1"
    )

    try:
        solicitud = Request(
            url,
            headers={
                "User-Agent": "SegundaVida/1.0"
            }
        )

        with urlopen(solicitud, timeout=5) as respuesta:

            datos = json.loads(
                respuesta.read().decode("utf-8")
            )

        if datos:

            latitud = float(datos[0]["lat"])
            longitud = float(datos[0]["lon"])

            return latitud, longitud

    except Exception:
        pass

    return None, None

def inicio(request):

    material_reutilizado_comunidad = (
        calcular_material_reutilizado_comunidad()
    )

    material_por_categoria = (
        calcular_material_reutilizado_por_categoria()
    )

    return render(
        request,
        "objetos/inicio.html",
        {
            "material_reutilizado_comunidad":
                material_reutilizado_comunidad,

            "material_por_categoria":
                material_por_categoria,
        }
    )

@login_required
def publicar_objeto(request):

    if request.method == "POST":

        formulario = ObjetoForm(request.POST)
        imagen_form = ImagenObjetoForm(request.POST, request.FILES)

        archivos = request.FILES.getlist("imagen")

        if len(archivos) > 5:
            messages.error(
                request,
                "Puedes subir un máximo de 5 imágenes por objeto."
            )
        elif formulario.is_valid():

            imagenes_validas = True

            for archivo in archivos:
                formulario_imagen = ImagenObjetoForm(
                    files={"imagen": archivo}
                )

                if not formulario_imagen.is_valid():
                    imagenes_validas = False
                    break

            if imagenes_validas:

                with transaction.atomic():

                    objeto = formulario.save(commit=False)
                    objeto.usuario = request.user

                    latitud = request.POST.get("latitud")
                    longitud = request.POST.get("longitud")

                    if latitud and longitud:
                        try:
                            objeto.latitud = float(latitud)
                            objeto.longitud = float(longitud)
                        except (TypeError, ValueError):
                            objeto.latitud = None
                            objeto.longitud = None
                    else:
                        latitud, longitud = geocodificar_ubicacion(
                            objeto.ubicacion
                        )

                        objeto.latitud = latitud
                        objeto.longitud = longitud

                    objeto.save()

                    for archivo in archivos:
                        ImagenObjeto.objects.create(
                            objeto=objeto,
                            imagen=archivo
                        )

                    # +1 karma por publicar un objeto
                    perfil = request.user.perfil
                    perfil.karma += 1
                    perfil.save(update_fields=["karma"])

                messages.success(
                    request,
                    "¡Objeto publicado correctamente!"
                )

                return redirect("inicio")

            else:
                messages.error(
                    request,
                    "Una o más imágenes no son válidas."
                )

    else:
        formulario = ObjetoForm()
        imagen_form = ImagenObjetoForm()

    return render(
        request,
        "objetos/publicar.html",
        {
            "formulario": formulario,
            "imagen_form": imagen_form,
        }
    )

def lista_objetos(request):
    objetos = Objeto.objects.filter(
        disponible=True
    ).select_related("categoria", "usuario").prefetch_related("imagenes")

    busqueda = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    estado = request.GET.get("estado", "")
    accion = request.GET.get("accion", "")

    if busqueda:
        objetos = objetos.filter(
            models.Q(nombre__icontains=busqueda)
            | models.Q(descripcion__icontains=busqueda)
            | models.Q(ubicacion__icontains=busqueda)
        )

    if categoria:
        objetos = objetos.filter(
            categoria_id=categoria
        )

    if estado:
        objetos = objetos.filter(
            estado=estado
        )

    if accion:
        objetos = objetos.filter(
            accion=accion
        )

    categorias = Categoria.objects.filter(
        activa=True
    ).order_by("nombre")

    return render(
        request,
        "objetos/lista.html",
        {
            "objetos": objetos,
            "busqueda": busqueda,
            "categoria": categoria,
            "estado": estado,
            "accion": accion,
            "categorias": categorias,
            "estados": Objeto.ESTADOS,
            "acciones": Objeto.ACCIONES,
        }
    )

def detalle_objeto(request, id):
    objeto = get_object_or_404(Objeto, id=id)

    material_reutilizado_estimado = (
        calcular_material_reutilizado_estimado(objeto)
    )

    return render(
        request,
        "objetos/detalle.html",
        {
            "objeto": objeto,
            "material_reutilizado_estimado": material_reutilizado_estimado,
        }
    )

@login_required
def editar_objeto(request, id):

    objeto = get_object_or_404(Objeto, id=id)

    if objeto.usuario != request.user:
        return redirect("lista_objetos")

    imagenes = objeto.imagenes.all()

    if request.method == "POST":

        formulario = ObjetoForm(
            request.POST,
            instance=objeto
        )

        imagen_form = ImagenObjetoForm(
            request.POST,
            request.FILES
        )

        archivos = request.FILES.getlist("imagen")

        eliminar_ids = request.POST.getlist(
            "eliminar_imagenes"
        )

        # Comprobar que las imágenes a eliminar
        # realmente pertenecen a este objeto
        imagenes_a_eliminar = ImagenObjeto.objects.filter(
            id__in=eliminar_ids,
            objeto=objeto
        )

        cantidad_restante = (
            imagenes.count()
            - imagenes_a_eliminar.count()
            + len(archivos)
        )

        if cantidad_restante > 5:

            messages.error(
                request,
                "Un objeto puede tener un máximo de 5 imágenes."
            )

        elif formulario.is_valid():

            imagenes_validas = True

            for archivo in archivos:

                formulario_imagen = ImagenObjetoForm(
                    files={"imagen": archivo}
                )

                if not formulario_imagen.is_valid():
                    imagenes_validas = False
                    break

            if imagenes_validas:

                with transaction.atomic():

                    objeto_actualizado = formulario.save(commit=False)

                    # Actualizar coordenadas según la nueva ubicación
                    latitud, longitud = geocodificar_ubicacion(
                        objeto_actualizado.ubicacion
                    )

                    objeto_actualizado.latitud = latitud
                    objeto_actualizado.longitud = longitud

                    objeto_actualizado.save()

                    # Eliminar imágenes seleccionadas
                    for imagen in imagenes_a_eliminar:

                        imagen.imagen.delete(
                            save=False
                        )

                        imagen.delete()

                    # Agregar nuevas imágenes
                    for archivo in archivos:

                        ImagenObjeto.objects.create(
                            objeto=objeto,
                            imagen=archivo
                        )

                messages.success(
                    request,
                    "¡Objeto actualizado correctamente!"
                )

                return redirect(
                    "detalle_objeto",
                    id=objeto.id
                )

            else:

                messages.error(
                    request,
                    "Una o más imágenes no son válidas."
                )

    else:

        formulario = ObjetoForm(
            instance=objeto
        )

        imagen_form = ImagenObjetoForm()

    return render(
        request,
        "objetos/editar.html",
        {
            "formulario": formulario,
            "imagen_form": imagen_form,
            "objeto": objeto,
            "imagenes": imagenes,
        }
    )

@login_required
def eliminar_objeto(request, id):

    objeto = get_object_or_404(Objeto, id=id)

    if objeto.usuario != request.user:
        return redirect("lista_objetos")

    if request.method == "POST":
        objeto.delete()
        return redirect("lista_objetos")

    return render(
        request,
        "objetos/eliminar.html",
        {"objeto": objeto}
    )

@login_required
def mis_objetos(request):

    objetos = Objeto.objects.filter(
        usuario=request.user
    ).order_by("-id")

    return render(
        request,
        "objetos/mis_objetos.html",
        {
            "objetos": objetos
        }
    )

def lugares_segunda_vida(request):

    categoria = request.GET.get("categoria", "")

    lugares = LugarSegundaVida.objects.filter(
        activo=True
    ).order_by("nombre")

    if categoria:
        lugares = [
            lugar for lugar in lugares
            if categoria in lugar.categorias
        ]

    categorias = [
        ("electronica", "Electrónica"),
        ("muebles", "Muebles"),
        ("ropa", "Ropa"),
        ("libros", "Libros"),
        ("juguetes", "Juguetes"),
        ("hogar", "Hogar"),
        ("otros", "Otros"),
    ]

    return render(
        request,
        "objetos/lugares_segunda_vida.html",
        {
            "lugares": lugares,
            "categorias": categorias,
            "categoria_seleccionada": categoria,
        }
    )
def detalle_lugar(request, lugar_id):

    lugar = get_object_or_404(
        LugarSegundaVida,
        id=lugar_id,
        activo=True
    )

    return render(
        request,
        "objetos/detalle_lugar.html",
        {
            "lugar": lugar
        }
    )