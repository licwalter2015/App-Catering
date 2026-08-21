from django import forms
from .models import Cliente


class WizardForm(forms.Form):
    """Formulario del wizard de cotización (5 pasos en uno)."""

    # Paso 1: Fecha
    fecha_evento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded-lg px-4 py-2 w-full'}),
        label='Fecha del evento',
    )

    # Paso 2: Invitados
    cantidad_invitados = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 1, 'class': 'border rounded-lg px-4 py-2 w-full'}),
        label='Cantidad de invitados',
    )

    # Paso 3: Menú (ServicioBase)
    servicio_base = forms.IntegerField(
        widget=forms.HiddenInput(),
        label='Servicio base',
    )

    # Paso 4: Adicionales (checkboxes dinámicos)
    # Se procesan en la vista como lista de IDs

    # Paso 4b: Zona de entrega
    zona_entrega = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
        label='Zona de entrega',
    )

    # Paso 5: Datos del cliente
    nombre = forms.CharField(
        max_length=180,
        widget=forms.TextInput(attrs={'class': 'border rounded-lg px-4 py-2 w-full'}),
        label='Nombre completo',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'border rounded-lg px-4 py-2 w-full'}),
        label='Email',
    )
    telefono = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'border rounded-lg px-4 py-2 w-full'}),
        label='Teléfono',
    )
    notas = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'border rounded-lg px-4 py-2 w-full'}),
        required=False,
        label='Notas adicionales',
    )
