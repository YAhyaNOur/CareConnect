from django.urls import path
from . import views

app_name = 'recherche'

urlpatterns = [
    path('', views.chercher_medecin, name='chercher_medecin'),
]
