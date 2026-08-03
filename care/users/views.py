from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import random
from users.models import Medecin

from users.models import (
    patient_insc,
    psy_insc,
    ConfPsy,
    Medecin,
    RDV,
    emp_auth
)

from users.forms import InscPsy, InscPatient, RDV_form



def home(request):
    return render(request, 'users/home.html')



def medecin_register(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        telephonenumber = request.POST.get('telephonenumber')
        specialite = request.POST.get('specialite')
        localisation_cabinet = request.POST.get('localisation_cabinet')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, "users/medecin/medecin_register.html", {
                'error': 'Les deux mots de passe sont différents'
            })

        if Medecin.objects.filter(email=email).exists():
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
            password=make_password(password)
        )

        code = str(random.randint(100000, 999999))
        medecin.verification_code = code
        medecin.save()

        send_mail(
            "Vérification de votre compte CareConnect",
            f"Bonjour Dr {medecin.firstname},\n\nVotre code de vérification est : {code}",
            settings.DEFAULT_FROM_EMAIL,
            [medecin.email],
            fail_silently=False,
        )

        return redirect('users:verify_mail')

    return render(request, "users/medecin/medecin_register.html")


def verify_mail(request):
    if request.method == "POST":
        email = request.POST.get("email")
        code = request.POST.get("code")

        try:
            medecin = Medecin.objects.get(email=email, verification_code=code)
            medecin.verification_code = None
            medecin.save()
            messages.success(request, "Compte vérifié avec succès.")
            return redirect("users:medecin_login")
        except Medecin.DoesNotExist:
            messages.error(request, "Code incorrect ou email invalide.")

    return render(request, "users/medecin/verify_mail.html")


def medecin_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        medecin = Medecin.objects.filter(email=email).first()

        if not medecin or not check_password(password, medecin.password):
            return render(request, "users/medecin/medecin_login.html", {
                "error": "Email ou mot de passe incorrect"
            })

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


#PATIENT 

def register_patient(request):
    if request.method == "POST":
        form = InscPatient(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get("my_password")
            passw = form.cleaned_data.get("passw")

            if password == passw:
                form.save()
                return redirect('users:login_patient')
            else:
                form.add_error("passw", "Les mots de passe ne correspondent pas")
    else:
        form = InscPatient()

    return render(request, "users/patient/register_patient.html", {"form": form})


def login_patient(request):
    if request.method == "POST":
        email = request.POST.get('my_email')
        password = request.POST.get('my_password')

        patient = patient_insc.objects.filter(
            my_email=email,
            my_password=password
        )

        if patient.exists():
            request.session['patient_email'] = email
            return redirect('users:interface_patient')
        else:
            messages.error(request, "Email ou mot de passe invalide")

    return render(request, 'users/patient/login_patient.html')




def interface_patient(request):
    specialite = request.GET.get('specialite', '')  
    medecins = []
    if specialite:
        medecins = Medecin.objects.filter(specialite__icontains=specialite)
    
    return render(request, "users/patient/patient_dashboard.html", {
        'medecins': medecins,
        'specialite': specialite
    })



def compte_patient(request):
    email = request.session.get('patient_email')
    patient = None
    if email:
        patient = patient_insc.objects.filter(my_email=email).first()
    return render(request, "users/Compte_patient.html", {"patient": patient})


# RDV 

def my_rdv(request):
    if request.method == "POST":
        form = RDV_form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:my_rdv')
    else:
        form = RDV_form()

    conf_psy = ConfPsy.objects.all()
    return render(request, "users/RDV_patient.html", {
        'form': form,
        'ConfPsy': conf_psy
    })


#Psy

def register_psy(request):
    file_url = None

    if request.method == "POST":
        form = InscPsy(request.POST, request.FILES)
        if form.is_valid():
            password = form.cleaned_data.get("password")
            passw = form.cleaned_data.get("passw")

            if password == passw:
                if request.FILES.get('fichiers'):
                    fs = FileSystemStorage()
                    file_name = fs.save(
                        request.FILES['fichiers'].name,
                        request.FILES['fichiers']
                    )
                    file_url = fs.url(file_name)

                form.save()
                return redirect('users:login_psy')
            else:
                form.add_error("passw", "Les mots de passe ne correspondent pas")
    else:
        form = InscPsy()

    return render(request, "users/psy/register_psy.html", {
        "form": form,
        "file_url": file_url
    })


def login_psy(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        psy = psy_insc.objects.filter(email=email, password=password)

        if psy.exists():
            return redirect('users:home')
        else:
            messages.error(request, "Email ou mot de passe invalide")

    return render(request, 'users/psy/login_psy.html')


def user_logout(request):
    request.session.flush()
    return redirect('users:home')
