from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session


class RegistroTemplateTests(TestCase):
    def test_registro_renderiza_campos_del_formulario(self):
        respuesta = self.client.get(reverse("registro"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="username"')
        self.assertContains(respuesta, 'name="email"')
        self.assertContains(respuesta, 'name="password"')
        self.assertContains(respuesta, 'name="password_confirmacion"')
        self.assertContains(respuesta, "Segunda Vida")

    def test_registro_muestra_error_de_contrasenas_distintas(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nueva-cuenta",
                "email": "nueva@example.com",
                "password": "una-clave-segura",
                "password_confirmacion": "otra-clave",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Las contraseñas no coinciden.")

    def test_registro_exitoso_asigna_grupo_usuario(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nueva-cuenta",
                "email": "nueva@example.com",
                "password": "ClaveSegura123!",
                "password_confirmacion": "ClaveSegura123!",
            },
        )

        self.assertRedirects(respuesta, reverse("inicio"))
        usuario = User.objects.get(username="nueva-cuenta")
        self.assertTrue(
            usuario.check_password("ClaveSegura123!")
        )
        self.assertTrue(
            usuario.groups.filter(name="Usuario").exists()
        )
        self.assertTrue(
            hasattr(usuario, "perfil")
        )


class LoginTemplateTests(TestCase):
    def test_login_renderiza_formulario_y_conserva_next(self):
        respuesta = self.client.get(
            reverse("login"),
            {"next": "/mis-objetos/"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="username"')
        self.assertContains(respuesta, 'name="password"')
        self.assertContains(respuesta, 'name="next"')
        self.assertContains(respuesta, "/mis-objetos/")
        self.assertContains(respuesta, "Regístrate")

    def test_login_muestra_error_de_credenciales_invalidas(self):
        respuesta = self.client.post(
            reverse("login"),
            {
                "username": "usuario-inexistente",
                "password": "clave-incorrecta",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].non_field_errors())
        self.assertContains(respuesta, 'class="auth-form-errors"')


class AdministrarUsuariosTests(TestCase):
    def setUp(self):
        self.administrador = User.objects.create_superuser(
            username="administrador",
            password="ClaveSegura123!",
        )
        self.usuario = User.objects.create_user(
            username="cuenta",
            password="ClaveSegura123!",
        )
        self.url = reverse("administrar_usuarios")
        self.client.force_login(self.administrador)

    def test_solo_administradores_pueden_acceder(self):
        respuesta = Client().get(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], reverse("login"))

        usuario_client = Client()
        usuario_client.force_login(self.usuario)
        respuesta = usuario_client.get(self.url)
        self.assertEqual(respuesta.status_code, 403)

    def test_pagina_muestra_roles_y_estado_de_cuenta(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Administrar usuarios")
        self.assertContains(respuesta, "Cuenta activa")
        self.assertContains(respuesta, 'name="accion" value="cambiar_rol"')
        self.assertContains(respuesta, 'name="accion" value="desactivar"')

    def test_administrador_puede_cambiar_rol(self):
        respuesta = self.client.post(
            self.url,
            {
                "username": self.usuario.username,
                "accion": "cambiar_rol",
                "rol": "Solo lectura",
            },
        )

        self.assertRedirects(respuesta, self.url)
        self.assertTrue(
            self.usuario.groups.filter(name="Solo lectura").exists()
        )
        self.assertTrue(Group.objects.filter(name="Solo lectura").exists())

    def test_desactivar_usuario_revoca_sus_sesiones_y_permite_reactivarlo(self):
        usuario_client = Client()
        usuario_client.force_login(self.usuario)
        session_key = usuario_client.session.session_key
        self.assertTrue(
            Session.objects.filter(session_key=session_key).exists()
        )

        respuesta = self.client.post(
            self.url,
            {
                "username": self.usuario.username,
                "accion": "desactivar",
            },
        )

        self.assertRedirects(respuesta, self.url)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)
        self.assertFalse(
            Session.objects.filter(session_key=session_key).exists()
        )

        respuesta = self.client.post(
            self.url,
            {
                "username": self.usuario.username,
                "accion": "reactivar",
            },
        )

        self.assertRedirects(respuesta, self.url)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_active)

    def test_no_se_puede_modificar_ni_desactivar_cuentas_administradoras(self):
        segundo_administrador = User.objects.create_superuser(
            username="otro-admin",
            password="ClaveSegura123!",
        )

        for username in (self.administrador.username, segundo_administrador.username):
            with self.subTest(username=username):
                respuesta = self.client.post(
                    self.url,
                    {
                        "username": username,
                        "accion": "desactivar",
                    },
                )
                self.assertRedirects(respuesta, self.url)

        self.administrador.refresh_from_db()
        segundo_administrador.refresh_from_db()
        self.assertTrue(self.administrador.is_active)
        self.assertTrue(segundo_administrador.is_active)
