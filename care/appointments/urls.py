# appointments/urls.py
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Calendrier et RDV
    path('events-json/', views.events_json, name='events_json'),
    path('today-appointments/', views.today_appointments, name='today_appointments'),
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # CRUD RDV
    path('add-rdv/', views.add_rdv, name='add_rdv'),
    path('update-appointment/<int:appointment_id>/', views.update_appointment, name='update_appointment'),
    path('delete-appointment/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('get-appointment-details/<int:appointment_id>/', views.get_appointment_details, name='get_appointment_details'),
    
    # Email
    path('send-appointment-email/<int:appointment_id>/', views.send_appointment_email, name='send_appointment_email'),
    
    # Fiche patient
    path('save-patient-file/<int:appointment_id>/', views.save_patient_file, name='save_patient_file'),
    
    # Patients
    path('patient-take-appointment/', views.patient_take_appointment, name='patient_take_appointment'),
    path('patient-appointments/', views.patient_appointments, name='patient_appointments'),
    path('recent-patients/', views.recent_patients, name='recent_patients'),
]