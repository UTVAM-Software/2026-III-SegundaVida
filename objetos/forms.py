
from django import forms
from .models import (
    Objeto,
    Categoria,
    ImagenObjeto,
    LugarSegundaVida,
)


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


class LugarSegundaVidaForm(forms.ModelForm):
    categorias = forms.CharField(
        required=False,
        label="Categorías",
        widget=forms.TextInput(attrs={
            "placeholder": "electronica, muebles, ropa",
        }),
        help_text="Escribe las categorías separadas por comas.",
    )

    class Meta:
        model = LugarSegundaVida
        fields = [
            "nombre",
            "descripcion",
            "tipo",
            "categorias",
            "servicios",
            "ubicacion",
            "telefono",
            "horario",
            "imagen",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "maxlength": 150,
                "placeholder": "Nombre del lugar",
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Describe qué ofrece este lugar",
            }),
            "servicios": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Servicios que ofrece",
            }),
            "ubicacion": forms.TextInput(attrs={
                "maxlength": 255,
                "placeholder": "Dirección o ubicación",
            }),
            "telefono": forms.TextInput(attrs={
                "maxlength": 20,
                "placeholder": "Teléfono de contacto",
            }),
            "horario": forms.TextInput(attrs={
                "maxlength": 255,
                "placeholder": "Ej. Lunes a viernes, 9:00 a 18:00",
            }),
            "imagen": forms.ClearableFileInput(attrs={
                "accept": "image/jpeg,image/png,image/webp",
            }),
        }

    def clean_categorias(self):
        categorias = self.cleaned_data.get("categorias")
        return [
            categoria.strip().lower()
            for categoria in categorias.split(",")
            if categoria.strip()
        ]

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if imagen and imagen.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "La imagen no puede superar los 5 MB."
            )
        return imagen
