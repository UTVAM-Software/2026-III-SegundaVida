from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse

from objetos.models import Objeto, Categoria
from usuarios.models import Perfil
from .models import Solicitud, Valoracion


class CentroSolicitudesTests(TestCase):
    def setUp(self):
        self.propietario = self.crear_usuario("propietario")
        self.solicitante = self.crear_usuario("solicitante")
        self.otro_propietario = self.crear_usuario("otro")
        self.categoria_hogar, _ = Categoria.objects.get_or_create(
            nombre="Hogar"
        )
        self.objeto_recibido = self.crear_objeto(
            self.propietario,
            "Silla",
        )
        self.objeto_solicitado = self.crear_objeto(
            self.otro_propietario,
            "Lámpara",
        )
        self.solicitud_recibida = Solicitud.objects.create(
            usuario=self.solicitante,
            objeto=self.objeto_recibido,
            mensaje="Me interesa",
        )
        self.solicitud_enviada = Solicitud.objects.create(
            usuario=self.propietario,
            objeto=self.objeto_solicitado,
            mensaje="La necesito",
        )
        self.client.force_login(self.propietario)

    def crear_usuario(self, username):
        usuario = User.objects.create_user(
            username=username,
            password="test-password",
        )
        Perfil.objects.create(
            usuario=usuario,
            nombre=username,
        )
        grupo_usuario, _ = Group.objects.get_or_create(
            name="Usuario"
        )
        usuario.groups.add(grupo_usuario)
        return usuario

    def crear_objeto(self, usuario, nombre):
        return Objeto.objects.create(
            usuario=usuario,
            nombre=nombre,
            descripcion=f"Descripción de {nombre}",
            categoria=self.categoria_hogar,
            estado="bueno",
            accion="donar",
            ubicacion="Tizayuca",
        )

    def test_pagina_recibidas_muestra_solo_solicitudes_recibidas(self):
        respuesta = self.client.get(reverse("solicitudes_recibidas"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            list(respuesta.context["solicitudes"]),
            [self.solicitud_recibida],
        )
        self.assertContains(respuesta, "Solicitudes recibidas")
        self.assertContains(respuesta, "Silla")
        self.assertNotContains(respuesta, "Lámpara")
        self.assertNotContains(respuesta, "Mis solicitudes")

    def test_participante_puede_abrir_formulario_de_valoracion(self):
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()

        respuesta = self.client.get(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.context["usuario_valorado"],
            self.solicitante
        )

    def test_valoracion_duplicada_no_se_permite(self):
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()

        Valoracion.objects.create(
            solicitud=self.solicitud_recibida,
            valorador=self.propietario,
            valorado=self.solicitante,
            puntuacion=5,
        )

        respuesta = self.client.get(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("mis_solicitudes")
        )
        self.assertEqual(Valoracion.objects.count(), 1)

    def test_puntuacion_fuera_de_rango_es_rechazada(self):
        from .forms import ValoracionForm

        formulario = ValoracionForm(
            data={
                "puntuacion": 6,
                "comentario": "Prueba de validación",
            }
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    def test_usuario_ajeno_no_puede_valorar(self):
        self.client.force_login(self.otro_propietario)
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()

        respuesta = self.client.get(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("mis_solicitudes")
        )
        self.assertEqual(Valoracion.objects.count(), 0)

    def test_usuario_ajeno_no_puede_enviar_valoracion(self):
        self.client.force_login(self.otro_propietario)
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()

        respuesta = self.client.post(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            ),
            {
                "puntuacion": 5,
                "comentario": "Intento de valoración ajena",
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("mis_solicitudes")
        )
        self.assertEqual(Valoracion.objects.count(), 0)

    def test_valoracion_valida_actualiza_karma_y_reputacion(self):
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()
        karma_inicial = self.propietario.perfil.karma

        respuesta = self.client.post(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            ),
            {
                "puntuacion": 4,
                "comentario": "Buena experiencia",
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("mis_solicitudes")
        )
        self.assertEqual(
            Valoracion.objects.filter(
                solicitud=self.solicitud_recibida,
                valorador=self.propietario,
                valorado=self.solicitante,
            ).count(),
            1
        )

        self.propietario.perfil.refresh_from_db()
        self.solicitante.perfil.refresh_from_db()
        self.assertEqual(
            self.propietario.perfil.karma,
            karma_inicial + 1
        )
        self.assertEqual(
            self.solicitante.perfil.reputacion,
            4.0
        )

    def test_puntuacion_invalida_no_guarda_valoracion_ni_modifica_karma(self):
        self.solicitud_recibida.estado = "cumplida"
        self.solicitud_recibida.save()
        karma_inicial = self.propietario.perfil.karma
        reputacion_inicial = self.solicitante.perfil.reputacion

        respuesta = self.client.post(
            reverse(
                "valorar_solicitud",
                args=[self.solicitud_recibida.id]
            ),
            {
                "puntuacion": 6,
                "comentario": "Puntuación inválida",
            }
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Valoracion.objects.count(), 0)
        self.propietario.perfil.refresh_from_db()
        self.solicitante.perfil.refresh_from_db()
        self.assertEqual(
            self.propietario.perfil.karma,
            karma_inicial
        )
        self.assertEqual(
            self.solicitante.perfil.reputacion,
            reputacion_inicial
        )
