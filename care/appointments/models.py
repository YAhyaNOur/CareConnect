from django.db import models
from django.utils import timezone
from users.models import Medecin, patient_insc  

class Appointment(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(patient_insc, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    patient_name = models.CharField(max_length=150)
    patient_email = models.EmailField(blank=True, null=True)
    patient_phone = models.CharField(max_length=30, blank=True, null=True)
    start_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_choices = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('rejected', 'Refusé'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')

    
    symptomes = models.TextField(blank=True, null=True)
    diagnostic = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    ordonnance = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient_name} - {self.medecin.firstname} {self.medecin.lastname} - {self.start_time}"
