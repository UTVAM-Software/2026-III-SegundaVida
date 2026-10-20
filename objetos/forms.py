
from django import forms
from .models import Objeto, Categoria, ImagenObjeto


class ObjetoForm(forms.ModelForm):

    class Meta:
        model = Objeto
        fields = [
            "nombre",
            "descripcion",
            "categoria",
            "estado",
            "accion",
            "funciona",
            "ubicacion",
        ]

        widgets = {
            "ubicacion": forms.TextInput(
                attrs={
                    "placeholder": "Ej. Tizayuca, Hidalgo",
                    "maxlength": 200,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["categoria"].queryset = Categoria.objects.filter(
            activa=True
        ).order_by("nombre")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ImagenObjetoForm(forms.ModelForm):

    class Meta:
        model = ImagenObjeto
        fields = ["imagen"]
        widgets = {
            "imagen": MultipleFileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp"
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["imagen"].required = False

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")

        if imagen:
            max_size = 5 * 1024 * 1024  # 5 MB

            if imagen.size > max_size:
                raise forms.ValidationError(
                    "La imagen no puede superar los 5 MB."
                )

        return imagen
