from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import json
from datetime import timedelta, datetime

from users.models import Medecin, patient_insc, psy_insc
from .models import Appointment, Avis
from .email_service import EmailService

def get_medecin_from_session(request):
    email = request.session.get('medecin_email')
    if not email:
        return None
    return Medecin.objects.filter(email=email).first()

def get_psy_from_session(request):
    email = request.session.get('psy_email')
    if not email:
        return None
    return psy_insc.objects.filter(email=email).first()

def get_patient_from_session(request):
    email = request.session.get('patient_email')
    if not email:
        return None
    return patient_insc.objects.filter(my_email=email).first()

def parse_datetime_safe(date_str):
    """Accepte une date ISO avec ou sans fuseau horaire."""
    if not date_str:
        return None
    dt = parse_datetime(date_str)
    if not dt:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

def events_json(request):
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse([], safe=False)

    if medecin:
        rdvs = Appointment.objects.filter(medecin=medecin)
    else:
        rdvs = Appointment.objects.filter(psy=psy)
        
    events = []
    for r in rdvs:
        if r.status == 'confirmed':
            bg_color = "#10b981"  # green
        elif r.status == 'rejected':
            bg_color = "#ef4444"  # red
        else:
            # Distinguish type for pending
            bg_color = "#4f46e5" if r.appointment_type == 'teleconsultation' else "#2563eb"
            
        type_str = "En ligne" if r.appointment_type == 'teleconsultation' else "Cabinet"
        events.append({
            "id": r.id,
            "title": f"RDV ({type_str}) - {r.patient_name}",
            "start": r.start_time.isoformat(),
            "end": (r.start_time + timedelta(minutes=30)).isoformat(),
            "backgroundColor": bg_color,
            "borderColor": bg_color,
            "textColor": "#ffffff",
            "extendedProps": {
                "patient": r.patient_name,
                "email": r.patient_email,
                "phone": r.patient_phone,
                "status": r.status,
                "type": r.appointment_type,
                "new_start_time": r.new_start_time.isoformat() if r.new_start_time else None,
                "reschedule_requested_by": r.reschedule_requested_by,
                "reschedule_reason": r.reschedule_reason,
            }
        })
    return JsonResponse(events, safe=False)

def today_appointments(request):
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse([], safe=False)

    today = timezone.now().date()
    if medecin:
        rdvs = Appointment.objects.filter(medecin=medecin, start_time__date=today).order_by('start_time')
    else:
        rdvs = Appointment.objects.filter(psy=psy, start_time__date=today).order_by('start_time')
        
    my_role = 'medecin' if medecin else 'psy'
    data = [{
        'id': r.id,
        'patient_name': r.patient_name,
        'patient_email': r.patient_email,
        'patient_phone': r.patient_phone,
        'start': r.start_time.isoformat(),
        'status': r.status,
        'type': r.appointment_type,
        'new_start_time': r.new_start_time.isoformat() if r.new_start_time else None,
        'reschedule_requested_by': r.reschedule_requested_by,
        'reschedule_reason': r.reschedule_reason,
        'my_role': my_role,
    } for r in rdvs]
    return JsonResponse(data, safe=False)

def add_rdv(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        data = json.loads(request.body)
        start_time = parse_datetime_safe(data['start'])
        if not start_time:
            return JsonResponse({"success": False, "message": "Date invalide"})
        
        if medecin:
            existing = Appointment.objects.filter(medecin=medecin, start_time=start_time).exists()
        else:
            existing = Appointment.objects.filter(psy=psy, start_time=start_time).exists()
            
        if existing:
            return JsonResponse({"success": False, "message": "Créneau déjà occupé"})
        
        patient_email = data.get('patient_email', '')
        patient = None
        if patient_email:
            patient = patient_insc.objects.filter(my_email=patient_email).first()
        
        if medecin:
            rdv = Appointment.objects.create(
                medecin=medecin,
                patient=patient,
                patient_name=data.get('patient_name', 'Nouveau Patient'),
                patient_email=patient_email,
                patient_phone=data.get('patient_phone', ''),
                start_time=start_time,
                appointment_type=data.get('appointment_type', 'cabinet'),
                status='pending'
            )
        else:
            rdv = Appointment.objects.create(
                psy=psy,
                patient=patient,
                patient_name=data.get('patient_name', 'Nouveau Patient'),
                patient_email=patient_email,
                patient_phone=data.get('patient_phone', ''),
                start_time=start_time,
                appointment_type=data.get('appointment_type', 'cabinet'),
                status='pending'
            )
        
        if patient_email:
            EmailService.send_appointment_email(rdv, action='confirm', doctor_message="Votre rendez-vous a été créé.")
        
        return JsonResponse({
            "success": True, 
            "id": rdv.id,
            "message": "Rendez-vous créé avec succès"
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})

def update_appointment(request, appointment_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        if medecin:
            rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        else:
            rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
            
        data = json.loads(request.body)
      
        if 'patient_name' in data:
            rdv.patient_name = data['patient_name']
        
        if 'start_time' in data:
            new_start = parse_datetime_safe(data['start_time'])
            if new_start:
                if new_start != rdv.start_time:
                    if medecin:
                        existing = Appointment.objects.filter(medecin=medecin, start_time=new_start).exclude(id=appointment_id).exists()
                    else:
                        existing = Appointment.objects.filter(psy=psy, start_time=new_start).exclude(id=appointment_id).exists()
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
            
        if 'appointment_type' in data:
            rdv.appointment_type = data['appointment_type']
        
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
                'status': rdv.status,
                'type': rdv.appointment_type
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

def delete_appointment(request, appointment_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        if medecin:
            rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        else:
            rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
            
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
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})
    
    try:
        if medecin:
            rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        else:
            rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
            
        data = {
            'id': rdv.id,
            'patient_name': rdv.patient_name,
            'patient_email': rdv.patient_email,
            'patient_phone': rdv.patient_phone,
            'start_time': rdv.start_time.isoformat(),
            'status': rdv.status,
            'appointment_type': rdv.appointment_type,
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
        medecin_id = data.get('medecin_id')
        psy_id = data.get('psy_id')
        appointment_type = data.get('appointment_type', 'cabinet')
        start_time = parse_datetime_safe(data.get('appointment_date'))
        
        if not start_time:
            return JsonResponse({'success': False, 'message': 'Date invalide'})
        
        if medecin_id:
            medecin = get_object_or_404(Medecin, id=medecin_id)
            existing_appointment = Appointment.objects.filter(
                medecin=medecin,
                start_time=start_time
            ).exists()
            
            if existing_appointment:
                return JsonResponse({'success': False, 'message': 'Ce créneau n\'est plus disponible'})
            
            rdv = Appointment.objects.create(
                medecin=medecin,
                patient=patient,
                patient_name=patient.Name,
                patient_email=patient.my_email,
                patient_phone=data.get('patient_phone', patient.NumTel),
                start_time=start_time,
                appointment_type=appointment_type,
                status='pending'
            )
        elif psy_id:
            psy = get_object_or_404(psy_insc, id=psy_id)
            existing_appointment = Appointment.objects.filter(
                psy=psy,
                start_time=start_time
            ).exists()
            
            if existing_appointment:
                return JsonResponse({'success': False, 'message': 'Ce créneau n\'est plus disponible'})
            
            rdv = Appointment.objects.create(
                psy=psy,
                patient=patient,
                patient_name=patient.Name,
                patient_email=patient.my_email,
                patient_phone=data.get('patient_phone', patient.NumTel),
                start_time=start_time,
                appointment_type=appointment_type,
                status='pending'
            )
        else:
            return JsonResponse({'success': False, 'message': 'Praticien non spécifié'})

        EmailService.send_appointment_email(rdv, action='confirm')

        return JsonResponse({
            'success': True, 
            'message': 'RDV pris avec succès!', 
            'id': rdv.id,
            'appointment_date': start_time.strftime('%d/%m/%Y %H:%M')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

def patient_file(request, patient_email):
    """Historique complet d'un patient (tous ses RDV + notes/diagnostics/ordonnances)
    avec le praticien actuellement connecté (médecin ou psy), consultable à tout moment."""
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})

    if medecin:
        rdvs = Appointment.objects.filter(medecin=medecin, patient_email=patient_email).order_by('-start_time')
    else:
        rdvs = Appointment.objects.filter(psy=psy, patient_email=patient_email).order_by('-start_time')

    if not rdvs.exists():
        return JsonResponse({'success': False, 'message': 'Aucun rendez-vous avec ce patient'})

    historique = [{
        'id': r.id,
        'start_time': r.start_time.isoformat(),
        'status': r.status,
        'type': r.appointment_type,
        'symptomes': r.symptomes or '',
        'diagnostic': r.diagnostic or '',
        'notes': r.notes or '',
        'ordonnance': r.ordonnance or '',
    } for r in rdvs]

    return JsonResponse({
        'success': True,
        'patient_name': rdvs.first().patient_name,
        'patient_email': patient_email,
        'patient_phone': rdvs.first().patient_phone,
        'historique': historique,
    })


def request_reschedule(request, appointment_id):
    """Le médecin, le psy ou le patient propose un nouveau créneau (report ou
    avancement) pour un RDV. Refusé si on est à moins de 24h du RDV actuel.
    L'autre partie doit ensuite accepter ou refuser via respond_reschedule."""
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    patient = get_patient_from_session(request)

    if not medecin and not psy and not patient:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})

    if medecin:
        requester_role = 'medecin'
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
    elif psy:
        requester_role = 'psy'
        rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
    else:
        requester_role = 'patient'
        rdv = get_object_or_404(Appointment, id=appointment_id, patient_email=patient.my_email)

    if rdv.status == 'rejected':
        return JsonResponse({'success': False, 'message': 'Ce rendez-vous a été refusé, impossible de le reporter.'})

    now = timezone.now()
    if rdv.start_time - now < timedelta(hours=24):
        return JsonResponse({
            'success': False,
            'message': "Ce rendez-vous a lieu dans moins de 24h : il ne peut plus être reporté ni avancé."
        })

    try:
        data = json.loads(request.body)
        new_start_time = parse_datetime_safe(data.get('new_start_time'))
        reason = (data.get('reason') or '').strip()

        if not new_start_time:
            return JsonResponse({'success': False, 'message': 'Nouvelle date invalide'})

        if new_start_time <= now:
            return JsonResponse({'success': False, 'message': 'La nouvelle date doit être dans le futur'})

        if rdv.medecin:
            conflit = Appointment.objects.filter(medecin=rdv.medecin, start_time=new_start_time).exclude(id=rdv.id).exists()
        else:
            conflit = Appointment.objects.filter(psy=rdv.psy, start_time=new_start_time).exclude(id=rdv.id).exists()

        if conflit:
            return JsonResponse({'success': False, 'message': 'Ce nouveau créneau est déjà occupé'})

        rdv.new_start_time = new_start_time
        rdv.reschedule_requested_by = requester_role
        rdv.reschedule_reason = reason
        rdv.save()

        EmailService.send_reschedule_request_email(rdv, requester_role)

        return JsonResponse({'success': True, 'message': 'Demande envoyée, en attente de confirmation par l\'autre partie.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})


def respond_reschedule(request, appointment_id):
    """La partie qui n'est pas à l'origine de la demande accepte ou refuse
    le report/avancement proposé."""
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    patient = get_patient_from_session(request)

    if not medecin and not psy and not patient:
        return JsonResponse({'success': False, 'message': 'Non authentifié'})

    if medecin:
        responder_role = 'medecin'
        rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
    elif psy:
        responder_role = 'psy'
        rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
    else:
        responder_role = 'patient'
        rdv = get_object_or_404(Appointment, id=appointment_id, patient_email=patient.my_email)

    if not rdv.new_start_time or not rdv.reschedule_requested_by:
        return JsonResponse({'success': False, 'message': 'Aucune demande de report en attente pour ce rendez-vous.'})

    if rdv.reschedule_requested_by == responder_role:
        return JsonResponse({'success': False, 'message': "Vous êtes à l'origine de cette demande : c'est à l'autre partie de répondre."})

    try:
        data = json.loads(request.body)
        decision = data.get('decision')

        requested_by = rdv.reschedule_requested_by

        if decision == 'accept':
            rdv.start_time = rdv.new_start_time
            rdv.new_start_time = None
            rdv.reschedule_requested_by = None
            rdv.reschedule_reason = ""
            rdv.save()
            EmailService.send_reschedule_response_email(rdv, accepted=True, requested_by=requested_by)
            return JsonResponse({'success': True, 'message': 'Nouveau créneau confirmé.'})
        elif decision == 'refuse':
            rdv.new_start_time = None
            rdv.reschedule_requested_by = None
            rdv.reschedule_reason = ""
            rdv.save()
            EmailService.send_reschedule_response_email(rdv, accepted=False, requested_by=requested_by)
            return JsonResponse({'success': True, 'message': 'Report refusé, le rendez-vous reste inchangé.'})
        else:
            return JsonResponse({'success': False, 'message': 'Décision invalide'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})


def recent_patients(request):
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse([], safe=False)

    from django.db.models import Max
    
    if medecin:
        subquery = Appointment.objects.filter(medecin=medecin)
    else:
        subquery = Appointment.objects.filter(psy=psy)
        
    subquery = subquery.values('patient_email').annotate(
        last_visit=Max('start_time')
    ).order_by('-last_visit')[:5]
    
    patients_list = []
    for item in subquery:
        if item['patient_email']:
            if medecin:
                last_rdv = Appointment.objects.filter(
                    medecin=medecin,
                    patient_email=item['patient_email']
                ).order_by('-start_time').first()
            else:
                last_rdv = Appointment.objects.filter(
                    psy=psy,
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
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        data = json.loads(request.body)
        action = data.get('action') 
        doctor_message = data.get('message', '')
        
        if action not in ['confirm', 'reject']:
            return JsonResponse({"success": False, "message": "Action invalide"})
        
        if medecin:
            rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        else:
            rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
        
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
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    try:
        if medecin:
            rdv = get_object_or_404(Appointment, id=appointment_id, medecin=medecin)
        else:
            rdv = get_object_or_404(Appointment, id=appointment_id, psy=psy)
            
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
    medecin = get_medecin_from_session(request)
    psy = get_psy_from_session(request)
    if not medecin and not psy:
        return JsonResponse({"success": False, "message": "Non authentifié"})
    
    today = timezone.now().date()
    
    if medecin:
        today_count = Appointment.objects.filter(
            medecin=medecin, 
            start_time__date=today
        ).count()
        
        patient_count = Appointment.objects.filter(
            medecin=medecin
        ).values('patient_email').distinct().count()
        
        first_day = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        confirmed_count = Appointment.objects.filter(
            medecin=medecin,
            status='confirmed',
            start_time__gte=first_day
        ).count()
        
        pending_count = Appointment.objects.filter(
            medecin=medecin, 
            status='pending'
        ).count()
    else:
        today_count = Appointment.objects.filter(
            psy=psy, 
            start_time__date=today
        ).count()
        
        patient_count = Appointment.objects.filter(
            psy=psy
        ).values('patient_email').distinct().count()
        
        first_day = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        confirmed_count = Appointment.objects.filter(
            psy=psy,
            status='confirmed',
            start_time__gte=first_day
        ).count()
        
        pending_count = Appointment.objects.filter(
            psy=psy, 
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
    patient = get_patient_from_session(request)
    if not patient:
        return JsonResponse([], safe=False)
    
    rdvs = Appointment.objects.filter(
        patient_email=patient.my_email
    ).order_by('-start_time')
    
    data = []
    for r in rdvs:
        if r.medecin:
            provider_name = f"Dr {r.medecin.firstname} {r.medecin.lastname}"
            specialite = r.medecin.specialite
            location = r.medecin.localisation_cabinet
        elif r.psy:
            provider_name = f"Psy {r.psy.Name}"
            specialite = "Psychologue"
            location = "Téléconsultation (En ligne)" if r.appointment_type == 'teleconsultation' else "Cabinet"
        else:
            provider_name = "Praticien de santé"
            specialite = "Spécialité"
            location = "Cabinet"

        deja_note = Avis.objects.filter(appointment=r).exists()
        peut_noter = (
            r.status == 'confirmed'
            and r.start_time <= timezone.now()
            and not deja_note
        )

        data.append({
            'id': r.id,
            'medecin_name': provider_name,
            'medecin_specialite': specialite,
            'start_time': r.start_time.isoformat(),
            'status': r.status,
            'location': location,
            'type': r.appointment_type,
            'deja_note': deja_note,
            'peut_noter': peut_noter,
            'diagnostic': r.diagnostic or '',
            'notes': r.notes or '',
            'ordonnance': r.ordonnance or '',
            'new_start_time': r.new_start_time.isoformat() if r.new_start_time else None,
            'reschedule_requested_by': r.reschedule_requested_by,
            'reschedule_reason': r.reschedule_reason or '',
        })
    
    return JsonResponse(data, safe=False)


def submit_avis(request, appointment_id):
    """Le patient note un praticien (médecin ou psy) après un rendez-vous confirmé et passé."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})

    patient = get_patient_from_session(request)
    if not patient:
        return JsonResponse({"success": False, "message": "Non authentifié"})

    rdv = get_object_or_404(Appointment, id=appointment_id, patient_email=patient.my_email)

    if rdv.status != 'confirmed':
        return JsonResponse({"success": False, "message": "Seuls les rendez-vous confirmés peuvent être notés."})
    if rdv.start_time > timezone.now():
        return JsonResponse({"success": False, "message": "Vous pourrez noter ce rendez-vous une fois qu'il aura eu lieu."})
    if Avis.objects.filter(appointment=rdv).exists():
        return JsonResponse({"success": False, "message": "Vous avez déjà noté ce rendez-vous."})

    try:
        data = json.loads(request.body)
        note = int(data.get('note', 0))
        commentaire = data.get('commentaire', '').strip()

        if note < 1 or note > 5:
            return JsonResponse({"success": False, "message": "La note doit être comprise entre 1 et 5."})

        Avis.objects.create(
            appointment=rdv,
            patient=patient,
            medecin=rdv.medecin,
            psy=rdv.psy,
            note=note,
            commentaire=commentaire,
        )

        return JsonResponse({"success": True, "message": "Merci pour votre avis !"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})