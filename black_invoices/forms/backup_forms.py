from django import forms


class DatabaseImportForm(forms.Form):
    backup_file = forms.FileField(
        label='Seleccionar archivo de respaldo (.json)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': '.json'})
    )