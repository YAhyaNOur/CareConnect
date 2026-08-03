from django.shortcuts import render
from users.models import Medecin

def chercher_medecin(request):
    specialite = request.GET.get('specialite', '')  
    medecins = []
    if specialite:
    
        medecins = Medecin.objects.filter(specialite__icontains=specialite)
    return render(request, 'recherche/chercher_medecin.html', {
        'medecins': medecins,
        'specialite': specialite
    })
