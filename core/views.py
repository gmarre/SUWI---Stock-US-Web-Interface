"""
Vue principale de l'application core.
"""
from django.http import HttpResponse


def home(request):
    """
    Vue pour la page d'accueil.
    Retourne un simple message "Hello World".
    """
    return HttpResponse("Hello World")
