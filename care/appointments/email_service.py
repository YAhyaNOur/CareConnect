from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags


class EmailService:
    @staticmethod
    def send_appointment_email(appointment, action='confirm', doctor_message=''):
        if not appointment.patient_email:
            return False

        try:
            medecin = appointment.medecin
            psy = appointment.psy
            appointment_date = appointment.start_time

            # Informations du praticien
            if medecin:
                provider_name = f"Dr. {medecin.firstname} {medecin.lastname}"
                specialite = medecin.specialite
                location = medecin.localisation_cabinet

            elif psy:
                provider_name = f"Psy. {psy.Name}"
                specialite = "Psychologue"
                location = (
                    "Téléconsultation (En ligne)"
                    if appointment.appointment_type == 'teleconsultation'
                    else "Cabinet"
                )

            else:
                provider_name = "Praticien de santé"
                specialite = "Spécialité"
                location = "Cabinet"

            context = {
                'patient_name': appointment.patient_name,
                'doctor_name': provider_name,
                'specialite': specialite,
                'location': location,
                'appointment_date': appointment_date.strftime('%d/%m/%Y'),
                'appointment_time': appointment_date.strftime('%H:%M'),
                'doctor_message': doctor_message,
                'appointment_id': appointment.id,
                'type': (
                    "Téléconsultation (En ligne)"
                    if appointment.appointment_type == 'teleconsultation'
                    else "Au cabinet"
                )
            }

            # Message du praticien
            doctor_message_html = ""

            if context['doctor_message']:
                doctor_message_html = (
                    '<p style="background-color: #f8fafc; '
                    'padding: 12px; '
                    'border-left: 4px solid #2563eb; '
                    'border-radius: 6px;">'
                    '<strong>Message du praticien :</strong> '
                    f"{context['doctor_message']}"
                    '</p>'
                )

            # Confirmation
            if action == 'confirm':
                subject = (
                    f"Confirmation de votre rendez-vous avec "
                    f"{context['doctor_name']}"
                )

                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">

                        <h2 style="color: #2563eb; margin-top: 0;">
                            Confirmation de votre rendez-vous
                        </h2>

                        <p>
                            Bonjour <strong>{context['patient_name']}</strong>,
                        </p>

                        <p>
                            Votre rendez-vous avec
                            <strong>{context['doctor_name']}</strong>
                            ({context['specialite']})
                            est confirmé pour le
                            <strong>
                                {context['appointment_date']}
                                à
                                {context['appointment_time']}
                            </strong>.
                        </p>

                        <p>
                            <strong>Type de consultation :</strong>
                            {context['type']}
                        </p>

                        <p>
                            <strong>Lieu :</strong>
                            {context['location']}
                        </p>

                        {doctor_message_html}

                        <p style="margin-top: 20px;">
                            Cordialement,<br>
                            L'équipe CareConnect
                        </p>

                    </div>
                </body>
                </html>
                """

            # Rejet / modification
            elif action == 'reject':
                subject = (
                    f"Modification de votre rendez-vous avec "
                    f"{context['doctor_name']}"
                )

                # Message spécifique au rejet
                doctor_message_html = ""

                if context['doctor_message']:
                    doctor_message_html = (
                        '<p style="background-color: #fef2f2; '
                        'padding: 12px; '
                        'border-left: 4px solid #dc2626; '
                        'border-radius: 6px;">'
                        '<strong>Raison / Message :</strong> '
                        f"{context['doctor_message']}"
                        '</p>'
                    )

                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">

                        <h2 style="color: #dc2626; margin-top: 0;">
                            Annulation / Modification de votre rendez-vous
                        </h2>

                        <p>
                            Bonjour <strong>{context['patient_name']}</strong>,
                        </p>

                        <p>
                            Votre rendez-vous avec
                            <strong>{context['doctor_name']}</strong>
                            prévu pour le
                            <strong>
                                {context['appointment_date']}
                                à
                                {context['appointment_time']}
                            </strong>
                            ne pourra malheureusement pas être honoré.
                        </p>

                        {doctor_message_html}

                        <p>
                            Veuillez prendre un nouveau rendez-vous
                            sur notre plateforme.
                        </p>

                        <p style="margin-top: 20px;">
                            Cordialement,<br>
                            L'équipe CareConnect
                        </p>

                    </div>
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

    @staticmethod
    def _recipient_for_role(appointment, role):
        """Retourne (email, nom_affiché) du destinataire correspondant au rôle
        ('patient', 'medecin' ou 'psy') pour ce rendez-vous."""
        if role == 'patient':
            return appointment.patient_email, appointment.patient_name
        elif role == 'medecin' and appointment.medecin:
            return appointment.medecin.email, f"Dr. {appointment.medecin.firstname} {appointment.medecin.lastname}"
        elif role == 'psy' and appointment.psy:
            return appointment.psy.email, f"Psy. {appointment.psy.Name}"
        return None, None

    @staticmethod
    def send_reschedule_request_email(appointment, requested_by):
        """Notifie l'autre partie qu'un report/avancement de RDV est proposé,
        et qu'elle doit l'accepter ou le refuser."""
        target_role = 'patient' if requested_by in ('medecin', 'psy') else (
            'medecin' if appointment.medecin else 'psy'
        )
        email, name = EmailService._recipient_for_role(appointment, target_role)
        if not email:
            return False

        requester_labels = {
            'medecin': 'Votre médecin',
            'psy': 'Votre psychologue',
            'patient': 'Le patient',
        }
        requester_label = requester_labels.get(requested_by, 'Une des parties')
        old_date = appointment.start_time.strftime('%d/%m/%Y à %H:%M')
        new_date = appointment.new_start_time.strftime('%d/%m/%Y à %H:%M')

        subject = "Proposition de report de votre rendez-vous"

        reason_html = ""
        if appointment.reschedule_reason:
            reason_html = (
                '<p style="background-color: #f8fafc; padding: 12px; '
                'border-left: 4px solid #2563eb; border-radius: 6px;">'
                f"<strong>Motif :</strong> {appointment.reschedule_reason}</p>"
            )

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                <h2 style="color: #2563eb; margin-top: 0;">Proposition de nouveau créneau</h2>
                <p>Bonjour <strong>{name}</strong>,</p>
                <p>{requester_label} propose de déplacer le rendez-vous prévu le
                    <strong>{old_date}</strong> au <strong>{new_date}</strong>.</p>
                {reason_html}
                <p>Merci de vous connecter sur CareConnect pour accepter ou refuser cette proposition.</p>
                <p style="margin-top: 20px;">Cordialement,<br>L'équipe CareConnect</p>
            </div>
        </body>
        </html>
        """
        plain_message = strip_tags(html_message)
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"❌ Erreur d'envoi d'email (demande de report): {e}")
            return False

    @staticmethod
    def send_reschedule_response_email(appointment, accepted, requested_by):
        """Notifie l'auteur de la demande de report que l'autre partie a
        accepté ou refusé sa proposition."""
        email, name = EmailService._recipient_for_role(appointment, requested_by)
        if not email:
            return False

        date_str = appointment.start_time.strftime('%d/%m/%Y à %H:%M')

        if accepted:
            subject = "Votre proposition de report a été acceptée"
            body_html = f'<p>Bonne nouvelle : le nouveau créneau du <strong>{date_str}</strong> a été accepté.</p>'
            title_color = "#16a34a"
        else:
            subject = "Votre proposition de report a été refusée"
            body_html = f'<p>Le report proposé a été refusé. Le rendez-vous reste fixé au <strong>{date_str}</strong>.</p>'
            title_color = "#dc2626"

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                <h2 style="color: {title_color}; margin-top: 0;">{subject}</h2>
                <p>Bonjour <strong>{name}</strong>,</p>
                {body_html}
                <p style="margin-top: 20px;">Cordialement,<br>L'équipe CareConnect</p>
            </div>
        </body>
        </html>
        """
        plain_message = strip_tags(html_message)
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"❌ Erreur d'envoi d'email (réponse au report): {e}")
            return False