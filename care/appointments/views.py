from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import json
from datetime import timedelta, datetime

from users.models import Medecin, patient_insc
from .models import Appointment
from .email_service import EmailService



def get_medecin_from_session(request):
  
    email = request.session.get('medecin_email')
    if not email:
        return None
    return Medecin.objects.filter(email=email).first()

def get_patient_from_session(request):
   
    email = request.session.get('patient_email')
    if not email:
        return None
    return patient_insc.objects.filter(my_email=email).first()

def parse_datetime_safe(date_str):
   
    dt = parse_datetime(date_str)
    if dt:
        return timezone.make_aware(dt)
    return None


def events_json(request):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse([], safe=False)

    rdvs = Appointment.objects.filter(medecin=medecin)
    events = []
    for r in rdvs:
       
        if r.status == 'confirmed':
            bg_color = "#00d97e"  
            border_color = "#00d97e"
        elif r.status == 'rejected':
            bg_color = "#e63757" 
            border_color = "#e63757"
        else:
            bg_color = "#2c7be5"  
            border_color = "#2c7be5"
            
        events.append({
            "id": r.id,
            "title": f"RDV - {r.patient_name}",
            "start": r.start_time.isoformat(),
            "end": (r.start_time + timedelta(minutes=30)).isoformat(),
            "backgroundColor": bg_color,
            "borderColor": border_color,
            "textColor": "#ffffff",
            "extendedProps": {
                "patient": r.patient_name,
                "email": r.patient_email,
                "phone": r.patient_phone,
                "status": r.status
            }
        })
    return JsonResponse(events, safe=False)

def today_appointments(request):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse([], safe=False)

    today = timezone.now().date()
    rdvs = Appointment.objects.filter(medecin=medecin, start_time__date=today).order_by('start_time')
    data = [{
        'id': r.id,
        'patient_name': r.patient_name,
        'patient_email': r.patient_email,
        'patient_phone': r.patient_phone,
        'start': r.start_time.isoformat(),
        'status': r.status
    } for r in rdvs]
    return JsonResponse(data, safe=False)




def add_rdv(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        data = json.loads(request.body)
        start_time = parse_datetime_safe(data['start'])
        if not start_time:
            return JsonResponse({"success": False, "message": "Date invalide"})
        
      
        existing_appointment = Appointment.objects.filter(
            medecin=medecin,
            start_time=start_time
        ).exists()
        
        if existing_appointment:
            return JsonResponse({"success": False, "message": "Créneau déjà occupé"})
        
     
        patient_email = data.get('patient_email', '')
        patient = None
        if patient_email:
            patient = patient_insc.objects.filter(my_email=patient_email).first()
        
     
        rdv = Appointment.objects.create(
            medecin=medecin,
            patient=patient,
            patient_name=data.get('patient_name', 'Nouveau Patient'),
            patient_email=patient_email,
            patient_phone=data.get('patient_phone', ''),
            start_time=start_time,
            status='pending'
        )
        
      
        if patient_email:
            EmailService.send_appointment_email(rdv, action='confirm', doctor_message="Votre rendez-vous a été créé.")
        
        return JsonResponse({
            "success": True, 
            "id": rdv.id,
            "message": "Rendez-vous créé avec succès"
        })
        
    except KeyError as e:
        return JsonResponse({"success": False, "message": f"Champ manquant: {e}"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})


def update_appointment(request, appointment_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        data = json.loads(request.body)
      
        if 'patient_name' in data:
            rdv.patient_name = data['patient_name']
        
        if 'start_time' in data:
            new_start = parse_datetime_safe(data['start_time'])
            if new_start:
             
                if new_start != rdv.start_time:
                    existing = Appointment.objects.filter(
                        medecin=medecin,
                        start_time=new_start
                    ).exclude(id=appointment_id).exists()
                    if existing:
                        return JsonResponse({'success': False, 'message': 'Créneau déjà occupé'})
                rdv.start_time = new_start
        
        if 'patient_email' in data:
            rdv.patient_email = data['patient_email']
         
            if data['patient_email']:
                patient = patient_insc.objects.filter(my_email=data['patient_email']).first()
                rdv.patient = patient
        
        if 'patient_phone' in data:
            rdv.patient_phone = data['patient_phone']
        
        if 'status' in data and data['status'] in ['pending', 'confirmed', 'rejected']:
            rdv.status = data['status']
        
        rdv.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Rendez-vous modifié avec succès!',
            'appointment': {
                'id': rdv.id,
                'patient_name': rdv.patient_name,
                'start_time': rdv.start_time.isoformat(),
                'status': rdv.status
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})


def delete_appointment(request, appointment_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        patient_name = rdv.patient_name
        rdv.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Rendez-vous avec {patient_name} supprimé avec succès!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

def get_appointment_details(request, appointment_id):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        data = {
            'id': rdv.id,
            'patient_name': rdv.patient_name,
            'patient_email': rdv.patient_email,
            'patient_phone': rdv.patient_phone,
            'start_time': rdv.start_time.isoformat(),
            'status': rdv.status,
            'symptomes': rdv.symptomes or '',
            'diagnostic': rdv.diagnostic or '',
            'notes': rdv.notes or '',
            'ordonnance': rdv.ordonnance or ''
        }
        return JsonResponse({'success': True, 'appointment': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})




def patient_take_appointment(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

    
    patient = get_patient_from_session(request)
    if not patient:
        return JsonResponse({'success': False, 'message': 'Veuillez vous connecter'})

    try:
        data = json.loads(request.body)
        medecin = get_object_or_404(Medecin, id=data.get('medecin_id'))
        start_time = parse_datetime_safe(data.get('appointment_date'))
        
        if not start_time:
            return JsonResponse({'success': False, 'message': 'Date invalide'})
        
     
        existing_appointment = Appointment.objects.filter(
            medecin=medecin,
            start_time=start_time
        ).exists()
        
        if existing_appointment:
            return JsonResponse({'success': False, 'message': 'Cet date n\'est plus disponible'})
        
  
        rdv = Appointment.objects.create(
            medecin=medecin,
            patient=patient,
            patient_name=patient.Name,
            patient_email=patient.my_email,
            patient_phone=data.get('patient_phone', patient.NumTel),
            start_time=start_time,
            status='pending'
        )

       
        EmailService.send_appointment_email(rdv, action='confirm')

        return JsonResponse({
            'success': True, 
            'message': 'RDV pris avec succès!', 
            'id': rdv.id,
            'appointment_date': start_time.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

def recent_patients(request):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse([], safe=False)

  
    from django.db.models import Max
    
 
    subquery = Appointment.objects.filter(
        medecin=medecin
    ).values('patient_email').annotate(
        last_visit=Max('start_time')
    ).order_by('-last_visit')[:5]
    
    patients_list = []
    for item in subquery:
        if item['patient_email']:
        
            last_rdv = Appointment.objects.filter(
                medecin=medecin,
                patient_email=item['patient_email']
            ).order_by('-start_time').first()
            
            if last_rdv:
            
                initials = '??'
                if last_rdv.patient_name:
                    parts = last_rdv.patient_name.split()
                    if len(parts) >= 2:
                        initials = f"{parts[0][0]}{parts[1][0]}".upper()
                    elif len(parts) == 1:
                        initials = parts[0][0].upper()
                
                patients_list.append({
                    'id': last_rdv.id,
                    'name': last_rdv.patient_name,
                    'initials': initials,
                    'last_visit': last_rdv.start_time.strftime('%d/%m/%Y'),
                    'email': last_rdv.patient_email,
                    'phone': last_rdv.patient_phone
                })
    
    return JsonResponse(patients_list, safe=False)




def send_appointment_email(request, appointment_id):
    """Vue pour envoyer un email de confirmation/refus"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        data = json.loads(request.body)
        action = data.get('action') 
        doctor_message = data.get('message', '')
        
        if action not in ['confirm', 'reject']:
            return JsonResponse({"success": False, "message": "Action invalide"})
        
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        
      
        if action == 'confirm':
            rdv.status = 'confirmed'
            rdv.save()
        elif action == 'reject':
            rdv.status = 'rejected'
            rdv.save()
        
        
        success = EmailService.send_appointment_email(
            rdv, 
            action=action, 
            doctor_message=doctor_message
        )
        
        if success:
            return JsonResponse({
                "success": True, 
                "message": f"Email {action} envoyé avec succès!",
                "status": rdv.status
            })
        else:
            return JsonResponse({
                "success": False, 
                "message": "Erreur lors de l'envoi de l'email",
                "status": rdv.status
            })
            
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return JsonResponse({"success": False, "message": str(e)})


def save_patient_file(request, appointment_id):
    """Vue pour sauvegarder la fiche patient"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        data = json.loads(request.body)
  
        if 'symptomes' in data:
            rdv.symptomes = data['symptomes']
        if 'diagnostic' in data:
            rdv.diagnostic = data['diagnostic']
        if 'notes' in data:
            rdv.notes = data['notes']
        if 'ordonnance' in data:
            rdv.ordonnance = data['ordonnance']
        
        rdv.save()
        
        return JsonResponse({
            "success": True, 
            "message": "Fiche patient sauvegardée avec succès!"
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def dashboard_stats(request):
    """Retourne les statistiques pour le dashboard"""
    medecin = get_medecin_from_session(request)
    if not medecin:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    today = timezone.now().date()
    
   
    today_count = Appointment.objects.filter(
        medecin=medecin, 
        start_time__date=today
    ).count()
    
 
    patient_count = Appointment.objects.filter(
        medecin=medecin
    ).values('patient_email').distinct().count()
    

    first_day = datetime.today().replace(day=1)
    confirmed_count = Appointment.objects.filter(
        medecin=medecin,
        status='confirmed',
        start_time__gte=first_day
    ).count()
    
    
    pending_count = Appointment.objects.filter(
        medecin=medecin, 
        status='pending'
    ).count()
    
    return JsonResponse({
        "success": True,
        "stats": {
            "today_appointments": today_count,
            "total_patients": patient_count,
            "monthly_confirmed": confirmed_count,
            "pending_appointments": pending_count
        }
    })


def patient_appointments(request):
    """Récupère les RDV d'un patient"""
    patient = get_patient_from_session(request)
    if not patient:
        return JsonResponse([], safe=False)
    
    rdvs = Appointment.objects.filter(
        patient_email=patient.my_email
    ).order_by('-start_time')
    
    data = [{
        'id': r.id,
        'medecin_name': f"Dr {r.medecin.firstname} {r.medecin.lastname}",
        'medecin_specialite': r.medecin.specialite,
        'start_time': r.start_time.isoformat(),
        'status': r.status,
        'location': r.medecin.localisation_cabinet
    } for r in rdvs]
    
    return JsonResponse(data, safe=False)