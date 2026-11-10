from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


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
