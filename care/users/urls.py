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
    path('medecin/verify_mail/resend/', views.resend_verification_code, name='resend_verification_code'),
    path('medecin/profil/', views.medecin_profile, name='medecin_profile'),

    # Patient
    path('patient/register/', views.register_patient, name='register_patient'),
    path('patient/login/', views.login_patient, name='login_patient'),
    path('patient/verify_mail/', views.verify_mail_patient, name='verify_mail_patient'),
    path('patient/verify_mail/resend/', views.resend_verification_code_patient, name='resend_verification_code_patient'),
    path('patient/interface/', views.interface_patient, name='interface_patient'),
    path('patient/compte/', views.compte_patient, name='compte_patient'),
    path('patient/rdv/', views.my_rdv, name='my_rdv'),

    # Psychologue
    path('psy/register/', views.register_psy, name='register_psy'),
    path('psy/login/', views.login_psy, name='login_psy'),
    path('psy/verify_mail/', views.verify_mail_psy, name='verify_mail_psy'),
    path('psy/verify_mail/resend/', views.resend_verification_code_psy, name='resend_verification_code_psy'),
    path('psy/dashboard/', views.psy_dashboard, name='psy_dashboard'),
    path('psy/profil/', views.psy_profile, name='psy_profile'),
    
    # Authentification commune
    path('logout/', views.user_logout, name='logout'),
]
