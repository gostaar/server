from django import forms

# Formulaire pour le fichier utilisé pour l'import des entreprises
class FileForm(forms.Form):
    file = forms.FileField()