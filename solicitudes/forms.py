from django import forms

from .models import Solicitud, Valoracion


class SolicitudForm(forms.ModelForm):

    class Meta:
        model = Solicitud
        fields = [
            "mensaje",
        ]

        labels = {
            "mensaje": "Mensaje para el propietario",
        }

        widgets = {
            "mensaje": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Cuéntale al propietario por qué te interesa "
                        "este objeto..."
                    ),
                }
            ),
        }

class ValoracionForm(forms.ModelForm):

    class Meta:
        model = Valoracion
        fields = ["puntuacion", "comentario"]

        labels = {
            "puntuacion": "Puntuación",
            "comentario": "Comentario",
        }

        widgets = {
            "puntuacion": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 5,
                }
            ),
            "comentario": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Cuéntanos cómo fue tu experiencia...",
                }
            ),
        }