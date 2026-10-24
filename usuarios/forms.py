from django import forms
from django.contrib.auth.models import User
from .models import Perfil

class RegistroForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )

    password_confirmacion = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar contraseña"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

        labels = {
            "username": "Usuario",
            "email": "Correo electrónico",
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirmacion = cleaned_data.get(
            "password_confirmacion"
        )

        if password and password_confirmacion:
            if password != password_confirmacion:
                raise forms.ValidationError(
                    "Las contraseñas no coinciden."
                )

        return cleaned_data
class PerfilForm(forms.ModelForm):

    class Meta:
        model = Perfil
        fields = [
            "nombre",
            "telefono",
            "ubicacion",
            "biografia",
        ]

        labels = {
            "nombre": "Nombre",
            "telefono": "Teléfono",
            "ubicacion": "Ubicación",
            "biografia": "Biografía",
        }

        widgets = {
            "biografia": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),
        }