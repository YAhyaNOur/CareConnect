from django.shortcuts import redirect
from urllib.parse import urlencode


def chercher_medecin(request):
    """Cette app 'recherche' est un ancien point d'entrée : la recherche par
    symptômes/proximité est désormais gérée par users.views.interface_patient
    (qui utilise les mêmes services d'analyse ci-dessous). On redirige donc
    ici plutôt que de dupliquer la logique et un template qui n'existe plus.
    """
    params = {}
    symptomes = request.GET.get('symptomes') or request.GET.get('specialite')
    if symptomes:
        params['symptomes'] = symptomes
    if request.GET.get('lat'):
        params['lat'] = request.GET.get('lat')
    if request.GET.get('lng'):
        params['lng'] = request.GET.get('lng')

    url = '/patient/interface/'
    if params:
        url += '?' + urlencode(params)
    return redirect(url)
