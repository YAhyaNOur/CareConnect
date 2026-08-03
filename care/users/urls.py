from django.urls import path
from . import views

app_name = "users" 

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),

    # Médecin
    path('medecin/dashboard/', views.medecin_dashboard, name='medecin_dashboard'),
   
    path('medecin/register/', views.medecin_register, name='medecin_register'),
    path('medecin/login/', views.medecin_login, name='medecin_login'),
    path('medecin/verify_mail/', views.verify_mail, name='verify_mail'),

    # Patient
    path('patient/register/', views.register_patient, name='register_patient'),
    path('patient/login/', views.login_patient, name='login_patient'),
    path('patient/interface/', views.interface_patient, name='interface_patient'),
    path('patient/compte/', views.compte_patient, name='compte_patient'),

    # Psychologue
    path('psy/register/', views.register_psy, name='register_psy'),
    path('psy/login/', views.login_psy, name='login_psy'),
    path('logout/', views.user_logout, name='logout'),

   
]
