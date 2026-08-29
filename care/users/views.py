from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
import random

from users.models import (
    patient_insc,
    psy_insc,
    Medecin,
)

from users.forms import InscPsy, InscPatient
from recherche.services import analyser_symptomes, enrichir_et_trier




def _parse_coordinate(value):
    """Convertit une coordonnée GPS en float sans faire planter le formulaire."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def home(request):
    return render(request, 'users/home.html')



def _envoyer_code_verification(instance, email, display_name):
    """Génère un nouveau code à 6 chiffres, le sauvegarde et l'envoie par email.
    Fonctionne pour Medecin, patient_insc et psy_insc (tous ont un champ
    verification_code)."""
    code = str(random.randint(100000, 999999))
    instance.verification_code = code
    instance.save()

    send_mail(
        "Vérification de votre compte CareConnect",
        f"Bonjour {display_name},\n\nVotre code de vérification est : {code}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def medecin_register(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = (request.POST.get('email') or '').strip().lower()
        telephonenumber = request.POST.get('telephonenumber')
        specialite = request.POST.get('specialite')
        localisation_cabinet = request.POST.get('localisation_cabinet')
        latitude = request.POST.get('latitude') or None
        longitude = request.POST.get('longitude') or None
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, "users/medecin/medecin_register.html", {
                'error': 'Les deux mots de passe sont différents'
            })

        if Medecin.objects.filter(email__iexact=email).exists():
            return render(request, "users/medecin/medecin_register.html", {
                'error': "Un compte avec cet email existe déjà"
            })

        medecin = Medecin.objects.create(
            firstname=firstname,
            lastname=lastname,
            email=email,
            telephonenumber=telephonenumber,
            specialite=specialite,
            localisation_cabinet=localisation_cabinet,
            latitude=latitude,
            longitude=longitude,
            password=make_password(password)
        )

        _envoyer_code_verification(medecin, medecin.email, f"Dr {medecin.firstname}")

        # On transmet l'email à la page de vérification pour que le médecin
        # n'ait pas à le retaper (source d'erreurs de frappe).
        return redirect(f"{reverse('users:verify_mail')}?email={medecin.email}")

    return render(request, "users/medecin/medecin_register.html")


def verify_mail(request):
    email_prefill = (request.GET.get("email") or "").strip().lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        code = (request.POST.get("code") or "").strip()
        email_prefill = email

        medecin = Medecin.objects.filter(email__iexact=email).first()

        if not medecin:
            messages.error(request, "Aucun compte médecin n'est associé à cet email.")
        elif medecin.verification_code is None:
            messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
            return redirect("users:medecin_login")
        elif medecin.verification_code != code:
            messages.error(request, "Code de vérification incorrect.")
        else:
            medecin.verification_code = None
            medecin.save()
            messages.success(request, "Compte vérifié avec succès. Vous pouvez vous connecter.")
            return redirect("users:medecin_login")

    return render(request, "users/medecin/verify_mail.html", {
        "email_prefill": email_prefill,
    })


def resend_verification_code(request):
    """Renvoie un nouveau code de vérification par email."""
    email = (request.POST.get("email") or request.GET.get("email") or "").strip().lower()
    medecin = Medecin.objects.filter(email__iexact=email).first()

    if not medecin:
        messages.error(request, "Aucun compte médecin n'est associé à cet email.")
    elif medecin.verification_code is None:
        messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
        return redirect("users:medecin_login")
    else:
        _envoyer_code_verification(medecin, medecin.email, f"Dr {medecin.firstname}")
        messages.success(request, "Un nouveau code vous a été envoyé par email.")

    return redirect(f"{reverse('users:verify_mail')}?email={email}")


def medecin_login(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password")

        medecin = Medecin.objects.filter(email__iexact=email).first()

        if not medecin or not check_password(password, medecin.password):
            return render(request, "users/medecin/medecin_login.html", {
                "error": "Email ou mot de passe incorrect"
            })

        if medecin.verification_code is not None:
            messages.error(request, "Veuillez d'abord vérifier votre email avant de vous connecter.")
            return redirect(f"{reverse('users:verify_mail')}?email={medecin.email}")

        request.session.flush()
        request.session['medecin_email'] = medecin.email
        return redirect('users:medecin_dashboard')

    return render(request, "users/medecin/medecin_login.html")
def get_medecin_from_session(request):
    """Récupère le médecin connecté depuis la session"""
    email = request.session.get('medecin_email')
    if not email:
        return None
    return Medecin.objects.filter(email=email).first()


def medecin_dashboard(request):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return redirect('users:medecin_login')  

  
    return render(request, 'users/medecin/dashboard.html', {
        'medecin': medecin
    })


def medecin_profile(request):
    medecin = get_medecin_from_session(request)
    if not medecin:
        return redirect('users:medecin_login')

    if request.method == "POST":
        medecin.firstname = request.POST.get('firstname', medecin.firstname)
        medecin.lastname = request.POST.get('lastname', medecin.lastname)
        medecin.telephonenumber = request.POST.get('telephonenumber', medecin.telephonenumber)
        medecin.specialite = request.POST.get('specialite', medecin.specialite)
        medecin.localisation_cabinet = request.POST.get('localisation_cabinet', medecin.localisation_cabinet)

        latitude_raw = request.POST.get('latitude')
        longitude_raw = request.POST.get('longitude')
        if latitude_raw not in (None, '') and longitude_raw not in (None, ''):
            latitude = _parse_coordinate(latitude_raw)
            longitude = _parse_coordinate(longitude_raw)
            if latitude is not None and longitude is not None:
                medecin.latitude = latitude
                medecin.longitude = longitude

        medecin.save()
        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('users:medecin_profile')

    return render(request, 'users/medecin/medecin_profile.html', {
        'medecin': medecin
    })


#PATIENT 

def register_patient(request):
    if request.method == "POST":
        form = InscPatient(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get("my_password")
            passw = form.cleaned_data.get("passw")

            if password == passw:
                patient = form.save(commit=False)
                # Les mots de passe ne doivent jamais être stockés en clair.
                patient.my_password = make_password(password)
                patient.passw = ""  # champ de confirmation, inutile après inscription
                patient.my_email = patient.my_email.strip().lower()
                patient.save()

                _envoyer_code_verification(patient, patient.my_email, patient.Name or "")

                return redirect(f"{reverse('users:verify_mail_patient')}?email={patient.my_email}")
            else:
                form.add_error("passw", "Les mots de passe ne correspondent pas")
    else:
        form = InscPatient()

    return render(request, "users/patient/register_patient.html", {"form": form})


def verify_mail_patient(request):
    email_prefill = (request.GET.get("email") or "").strip().lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        code = (request.POST.get("code") or "").strip()
        email_prefill = email

        patient = patient_insc.objects.filter(my_email__iexact=email).first()

        if not patient:
            messages.error(request, "Aucun compte patient n'est associé à cet email.")
        elif patient.verification_code is None:
            messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
            return redirect("users:login_patient")
        elif patient.verification_code != code:
            messages.error(request, "Code de vérification incorrect.")
        else:
            patient.verification_code = None
            patient.save()
            messages.success(request, "Compte vérifié avec succès. Vous pouvez vous connecter.")
            return redirect("users:login_patient")

    return render(request, "users/patient/verify_mail.html", {
        "email_prefill": email_prefill,
    })


def resend_verification_code_patient(request):
    email = (request.POST.get("email") or request.GET.get("email") or "").strip().lower()
    patient = patient_insc.objects.filter(my_email__iexact=email).first()

    if not patient:
        messages.error(request, "Aucun compte patient n'est associé à cet email.")
    elif patient.verification_code is None:
        messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
        return redirect("users:login_patient")
    else:
        _envoyer_code_verification(patient, patient.my_email, patient.Name or "")
        messages.success(request, "Un nouveau code vous a été envoyé par email.")

    return redirect(f"{reverse('users:verify_mail_patient')}?email={email}")


def login_patient(request):
    if request.method == "POST":
        email = (request.POST.get('my_email') or '').strip().lower()
        password = request.POST.get('my_password') or ''

        patient = patient_insc.objects.filter(my_email__iexact=email).first()
        authenticated = False

        if patient:
            try:
                authenticated = check_password(password, patient.my_password)
            except Exception:
                authenticated = False

            if not authenticated and patient.my_password == password:
                # Compte créé avant la migration vers les mots de passe hashés :
                # on authentifie une dernière fois avec l'ancienne valeur en clair,
                # puis on la remplace immédiatement par un mot de passe hashé.
                authenticated = True
                patient.my_password = make_password(password)
                patient.save(update_fields=['my_password'])

        if authenticated and patient.verification_code is not None:
            messages.error(request, "Veuillez d'abord vérifier votre email avant de vous connecter.")
            return redirect(f"{reverse('users:verify_mail_patient')}?email={patient.my_email}")

        if authenticated:
            request.session.flush()
            request.session['patient_email'] = patient.my_email
            return redirect('users:interface_patient')
        else:
            messages.error(request, "Email ou mot de passe invalide")

    return render(request, 'users/patient/login_patient.html')




def interface_patient(request):
    symptomes = request.GET.get('symptomes', '').strip()
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    # Si le patient est connecté et nous envoie sa position, on la met à jour
    # pour pouvoir la réutiliser plus tard (ex: page psy) sans redemander.
    patient_email = request.session.get('patient_email')
    if patient_email and lat and lng:
        patient_insc.objects.filter(my_email=patient_email).update(
            latitude=lat, longitude=lng
        )
    elif patient_email and (not lat or not lng):
        # pas de position transmise dans l'URL : on retombe sur celle enregistrée
        patient = patient_insc.objects.filter(my_email=patient_email).first()
        if patient and patient.latitude is not None:
            lat, lng = patient.latitude, patient.longitude

    specialite_trouvee = ''
    medecins = []
    if symptomes:
        specialite_trouvee = analyser_symptomes(symptomes)
        medecins = Medecin.objects.filter(specialite__icontains=specialite_trouvee)
        medecins = enrichir_et_trier(medecins, lat, lng, type_praticien='medecin')

    return render(request, "users/patient/patient_dashboard.html", {
        'medecins': medecins,
        'symptomes': symptomes,
        'specialite_trouvee': specialite_trouvee,
    })



def compte_patient(request):
    email = request.session.get('patient_email')
    patient = None
    if email:
        patient = patient_insc.objects.filter(my_email=email).first()
    return render(request, "users/Compte_patient.html", {"patient": patient})


# RDV 

def my_rdv(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    patient_email = request.session.get('patient_email')
    if patient_email and lat and lng:
        patient_insc.objects.filter(my_email=patient_email).update(
            latitude=lat, longitude=lng
        )
    elif patient_email and (not lat or not lng):
        patient = patient_insc.objects.filter(my_email=patient_email).first()
        if patient and patient.latitude is not None:
            lat, lng = patient.latitude, patient.longitude

    psychologues = psy_insc.objects.all()
    psychologues = enrichir_et_trier(psychologues, lat, lng, type_praticien='psy')

    return render(request, "users/RDV_patient.html", {
        'psychologues': psychologues
    })


#Psy

def register_psy(request):
    if request.method == "POST":
        form = InscPsy(request.POST, request.FILES)
        if form.is_valid():
            password = form.cleaned_data.get("password")
            passw = form.cleaned_data.get("passw")

            if password == passw:
                # form.save() gère déjà la sauvegarde du fichier "fichiers" via
                # le FileField (on ne le sauvegarde plus une seconde fois à la main).
                psy = form.save(commit=False)
                psy.password = make_password(password)
                psy.passw = ""  # champ de confirmation, inutile après inscription
                psy.email = psy.email.strip().lower()
                psy.save()

                _envoyer_code_verification(psy, psy.email, psy.Name or "")

                return redirect(f"{reverse('users:verify_mail_psy')}?email={psy.email}")
            else:
                form.add_error("passw", "Les mots de passe ne correspondent pas")
    else:
        form = InscPsy()

    return render(request, "users/psy/register_psy.html", {
        "form": form
    })


def verify_mail_psy(request):
    email_prefill = (request.GET.get("email") or "").strip().lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        code = (request.POST.get("code") or "").strip()
        email_prefill = email

        psy = psy_insc.objects.filter(email__iexact=email).first()

        if not psy:
            messages.error(request, "Aucun compte psychologue n'est associé à cet email.")
        elif psy.verification_code is None:
            messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
            return redirect("users:login_psy")
        elif psy.verification_code != code:
            messages.error(request, "Code de vérification incorrect.")
        else:
            psy.verification_code = None
            psy.save()
            messages.success(request, "Compte vérifié avec succès. Vous pouvez vous connecter.")
            return redirect("users:login_psy")

    return render(request, "users/psy/verify_mail.html", {
        "email_prefill": email_prefill,
    })


def resend_verification_code_psy(request):
    email = (request.POST.get("email") or request.GET.get("email") or "").strip().lower()
    psy = psy_insc.objects.filter(email__iexact=email).first()

    if not psy:
        messages.error(request, "Aucun compte psychologue n'est associé à cet email.")
    elif psy.verification_code is None:
        messages.info(request, "Ce compte est déjà vérifié. Vous pouvez vous connecter.")
        return redirect("users:login_psy")
    else:
        _envoyer_code_verification(psy, psy.email, psy.Name or "")
        messages.success(request, "Un nouveau code vous a été envoyé par email.")

    return redirect(f"{reverse('users:verify_mail_psy')}?email={email}")


def login_psy(request):
    if request.method == "POST":
        email = (request.POST.get('my_email') or request.POST.get('email') or '').strip().lower()
        password = request.POST.get('my_password') or request.POST.get('password') or ''

        psy = psy_insc.objects.filter(email__iexact=email).first()
        authenticated = False

        if psy:
            try:
                authenticated = check_password(password, psy.password)
            except Exception:
                authenticated = False

            if not authenticated and psy.password == password:
                # Compte créé avant la migration vers les mots de passe hashés.
                authenticated = True
                psy.password = make_password(password)
                psy.save(update_fields=['password'])

        if authenticated and psy.verification_code is not None:
            messages.error(request, "Veuillez d'abord vérifier votre email avant de vous connecter.")
            return redirect(f"{reverse('users:verify_mail_psy')}?email={psy.email}")

        if authenticated:
            request.session.flush()
            request.session['psy_email'] = psy.email
            return redirect('users:psy_dashboard')
        else:
            messages.error(request, "Email ou mot de passe invalide")

    return render(request, 'users/psy/login_psy.html')


def psy_dashboard(request):
    email = request.session.get('psy_email')
    if not email:
        return redirect('users:login_psy')
    
    psy = psy_insc.objects.filter(email=email).first()
    if not psy:
        return redirect('users:login_psy')
        
    return render(request, 'users/psy/dashboard.html', {
        'psy': psy
    })


def psy_profile(request):
    email = request.session.get('psy_email')
    if not email:
        return redirect('users:login_psy')

    psy = psy_insc.objects.filter(email=email).first()
    if not psy:
        return redirect('users:login_psy')

    if request.method == "POST":
        psy.Name = request.POST.get('Name', psy.Name)
        psy.localisation_cabinet = request.POST.get('localisation_cabinet', psy.localisation_cabinet)

        latitude_raw = request.POST.get('latitude')
        longitude_raw = request.POST.get('longitude')
        if latitude_raw not in (None, '') and longitude_raw not in (None, ''):
            latitude = _parse_coordinate(latitude_raw)
            longitude = _parse_coordinate(longitude_raw)
            if latitude is not None and longitude is not None:
                psy.latitude = latitude
                psy.longitude = longitude

        if request.FILES.get('fichiers'):
            psy.fichiers = request.FILES['fichiers']

        psy.save()
        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('users:psy_profile')

    return render(request, 'users/psy/psy_profile.html', {
        'psy': psy
    })


def user_logout(request):
    request.session.flush()
    return redirect('users:home')
