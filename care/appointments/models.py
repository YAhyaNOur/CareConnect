from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Medecin, patient_insc, psy_insc  

class Appointment(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    psy = models.ForeignKey(psy_insc, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    patient = models.ForeignKey(patient_insc, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    patient_name = models.CharField(max_length=150)
    patient_email = models.EmailField(blank=True, null=True)
    patient_phone = models.CharField(max_length=30, blank=True, null=True)
    start_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    appointment_type_choices = [
        ('cabinet', 'Au cabinet'),
        ('teleconsultation', 'Téléconsultation'),
    ]
    appointment_type = models.CharField(max_length=20, choices=appointment_type_choices, default='cabinet')
    
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

    # Report / avancement de RDV : une partie (médecin, psy ou patient) propose
    # une nouvelle date, l'autre partie doit l'accepter ou la refuser.
    reschedule_requested_by_choices = [
        ('medecin', 'Médecin'),
        ('psy', 'Psychologue'),
        ('patient', 'Patient'),
    ]
    new_start_time = models.DateTimeField(null=True, blank=True)
    reschedule_requested_by = models.CharField(
        max_length=10, choices=reschedule_requested_by_choices, null=True, blank=True
    )
    reschedule_reason = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        provider = f"Dr {self.medecin.firstname} {self.medecin.lastname}" if self.medecin else f"Psy {self.psy.Name}"
        return f"{self.patient_name} - {provider} - {self.start_time}"


class Avis(models.Model):
    """Note et commentaire laissés par un patient après un rendez-vous (médecin ou psy)."""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='avis')
    patient = models.ForeignKey(patient_insc, on_delete=models.CASCADE, related_name='avis_laisses', null=True, blank=True)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='avis', null=True, blank=True)
    psy = models.ForeignKey(psy_insc, on_delete=models.CASCADE, related_name='avis', null=True, blank=True)
    note = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        cible = f"Dr {self.medecin}" if self.medecin else f"Psy {self.psy}"
        return f"Avis {self.note}/5 - {cible}"
