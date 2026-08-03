from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailService:
    @staticmethod
    def send_appointment_email(appointment, action='confirm', doctor_message=''):
        if not appointment.patient_email:
            return False
        
        try:
            medecin = appointment.medecin
            appointment_date = appointment.start_time
            
           
            context = {
                'patient_name': appointment.patient_name,
                'doctor_name': f"Dr {medecin.firstname} {medecin.lastname}",
                'specialite': medecin.specialite,
                'location': medecin.localisation_cabinet,
                'appointment_date': appointment_date.strftime('%A %d %B %Y'),
                'appointment_time': appointment_date.strftime('%H:%M'),
                'doctor_message': doctor_message,
                'appointment_id': appointment.id
            }
            
            if action == 'confirm':
                subject = f'Confirmation de votre rendez-vous avec {context["doctor_name"]}'
               
                html_message = f"""
                <html>
                <body>
                    <h2>Confirmation de votre rendez-vous</h2>
                    <p>Bonjour {context['patient_name']},</p>
                    <p>Votre rendez-vous avec <strong>{context['doctor_name']}</strong> ({context['specialite']}) 
                    est confirmé pour le <strong>{context['appointment_date']} à {context['appointment_time']}</strong>.</p>
                    <p><strong>Lieu :</strong> {context['location']}</p>
                    {f"<p><strong>Message du médecin :</strong> {context['doctor_message']}</p>" if context['doctor_message'] else ""}
                    <p>Cordialement,<br>L'équipe CareConnect</p>
                </body>
                </html>
                """
            elif action == 'reject':
                subject = f'Modification de votre rendez-vous avec {context["doctor_name"]}'
                html_message = f"""
                <html>
                <body>
                    <h2>Modification de votre rendez-vous</h2>
                    <p>Bonjour {context['patient_name']},</p>
                    <p>Votre rendez-vous avec <strong>{context['doctor_name']}</strong> prévu pour le 
                    <strong>{context['appointment_date']} à {context['appointment_time']}</strong> 
                    ne pourra pas être honoré.</p>
                    {f"<p><strong>Raison :</strong> {context['doctor_message']}</p>" if context['doctor_message'] else ""}
                    <p>Veuillez prendre un nouveau rendez-vous sur notre plateforme.</p>
                    <p>Cordialement,<br>L'équipe CareConnect</p>
                </body>
                </html>
                """
            else:
                return False
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur d'envoi d'email: {e}")
            return False