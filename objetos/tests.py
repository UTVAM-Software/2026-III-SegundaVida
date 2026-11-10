from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse

from .models import Objeto, Categoria


class InicioTests(TestCase):

    def test_inicio_renderiza_busqueda_e_impacto(self):
        respuesta = self.client.get(reverse("inicio"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta,
            f'href="{reverse("lista_objetos")}"',
        )
        self.assertContains(
            respuesta,
            "IMPACTO DE LA COMUNIDAD",
        )
        self.assertContains(respuesta, "Crear cuenta")


class ListaObjetosTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="comunidad",
            password="prueba-segura",
        )

        grupo_usuario, _ = Group.objects.get_or_create(
            name="Usuario"
        )
        self.usuario.groups.add(grupo_usuario)

        self.electronica = Categoria.objects.create(
            nombre="Electrónica"
        )
        self.libros = Categoria.objects.create(
            nombre="Libros"
        )
        self.ropa = Categoria.objects.create(
            nombre="Ropa"
        )

        self.radio = self.crear_objeto(
            "Radio",
            self.electronica,
            "bueno",
            "donar",
        )

        self.libro = self.crear_objeto(
            "Novela",
            self.libros,
            "nuevo",
            "intercambiar",
        )

        self.crear_objeto(
            "Chaqueta",
            self.ropa,
            "regular",
            "reparar",
            disponible=False,
        )

    def crear_objeto(
        self,
        nombre,
        categoria,
        estado,
        accion,
        disponible=True,
    ):
        return Objeto.objects.create(
            usuario=self.usuario,
            nombre=nombre,
            descripcion=f"Descripción de {nombre}",
            categoria=categoria,
            estado=estado,
            accion=accion,
            disponible=disponible,
        )

    def test_lista_filtra_por_varias_categorias(self):
        respuesta = self.client.get(
            reverse("lista_objetos"),
            {
                "categoria": [
                    str(self.electronica.id),
                    str(self.libros.id),
                ]
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            {objeto.id for objeto in respuesta.context["objetos"]},
            {self.radio.id, self.libro.id},
        )

        self.assertEqual(
            respuesta.context["cantidad_objetos"],
            2,
        )

    def test_lista_filtra_por_una_categoria(self):
        respuesta = self.client.get(
            reverse("lista_objetos"),
            {"categoria": str(self.electronica.id)},
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            [objeto.id for objeto in respuesta.context["objetos"]],
            [self.radio.id],
        )

        self.assertContains(respuesta, "Electrónica")

    def test_lista_filtra_por_estado_y_accion(self):
        respuesta = self.client.get(
            reverse("lista_objetos"),
            {
                "estado": "bueno",
                "accion": "donar",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            [objeto.id for objeto in respuesta.context["objetos"]],
            [self.radio.id],
        )

    def test_lista_busca_por_nombre(self):
        respuesta = self.client.get(
            reverse("lista_objetos"),
            {"q": "Radio"},
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            [objeto.id for objeto in respuesta.context["objetos"]],
            [self.radio.id],
        )

        self.assertEqual(
            respuesta.context["cantidad_objetos"],
            1,
        )

    def test_lista_muestra_maximo_10_objetos_por_pagina(self):
        for numero in range(9):
            self.crear_objeto(
                f"Objeto {numero}",
                self.electronica,
                "bueno",
                "donar",
            )

        primera_pagina = self.client.get(
            reverse("lista_objetos")
        )

        segunda_pagina = self.client.get(
            reverse("lista_objetos"),
            {"page": 2},
        )

        self.assertEqual(
            len(primera_pagina.context["objetos"]),
            10,
        )

        self.assertEqual(
            len(segunda_pagina.context["objetos"]),
            1,
        )

    def test_paginacion_conserva_filtros_activos(self):
        for numero in range(10):
            self.crear_objeto(
                f"Objeto {numero}",
                self.electronica,
                "bueno",
                "donar",
            )

        respuesta = self.client.get(
            reverse("lista_objetos"),
            {"categoria": str(self.electronica.id)},
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertContains(
            respuesta,
            f"categoria={self.electronica.id}&amp;page=2",
        )

    def test_lista_ignora_parametros_invalidos(self):
        respuesta = self.client.get(
            reverse("lista_objetos"),
            {
                "categoria": [
                    "electronica",
                    "99999",
                ],
                "estado": "inventado",
                "accion": "hackear",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["cantidad_objetos"],
            2,
        )

        self.assertEqual(
            list(respuesta.context["categorias_seleccionadas"]),
            [],
        )

        self.assertEqual(
            list(respuesta.context["estados_seleccionados"]),
            [],
        )

        self.assertEqual(
            list(respuesta.context["acciones_seleccionadas"]),
            [],
        )

    def test_publicar_conserva_mapa_y_vista_previa_de_imagenes(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(
            reverse("publicar_objeto")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertContains(
            respuesta,
            'id="mapa-publicar"',
        )

        self.assertContains(
            respuesta,
            'id="previsualizacion-imagenes"',
        )
