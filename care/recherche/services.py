"""
Services pour la recherche de praticiens :
- analyse des symptômes du patient via l'API Gemini pour déterminer la spécialité médicale adéquate
- calcul de distance GPS (formule de Haversine) pour trier les praticiens par proximité
"""
import math
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Liste fermée des spécialités que l'on autorise en sortie du modèle,
# pour rester cohérent avec ce que les médecins renseignent à l'inscription.
SPECIALITES_CONNUES = [
    "Généraliste",
    "Cardiologue",
    "Dermatologue",
    "Pédiatre",
    "Gynécologue",
    "ORL",
    "Ophtalmologue",
    "Dentiste",
    "Gastro-entérologue",
    "Neurologue",
    "Rhumatologue",
    "Endocrinologue",
    "Pneumologue",
    "Urologue",
    "Psychiatre",
]


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance en kilomètres entre deux points GPS (formule de Haversine)."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    except (TypeError, ValueError):
        return None

    r = 6371.0  # rayon moyen de la Terre en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 1)
def analyser_symptomes(symptomes: str) -> str:
    """
    Envoie les symptômes décrits par le patient à l'API Gemini et retourne
    la spécialité médicale la plus adaptée, choisie parmi SPECIALITES_CONNUES.
    Repli sur "Généraliste" en cas d'erreur, de clé API absente, ou de réponse
    hors-liste (cas le plus sûr par défaut).
    """
    symptomes = (symptomes or "").strip()
    if not symptomes:
        return "Généraliste"

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        logger.warning("GEMINI_API_KEY non configurée : repli sur Généraliste.")
        return "Généraliste"

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")

        prompt = (
            "Tu es un système d'orientation médicale (triage), pas un médecin. "
            "Un patient décrit ses symptômes ci-dessous. Choisis UNE SEULE spécialité "
            "parmi cette liste exacte, sans en inventer d'autres :\n"
            f"{', '.join(SPECIALITES_CONNUES)}\n\n"
            f"Symptômes du patient : \"{symptomes}\"\n\n"
            "Réponds uniquement avec le nom exact de la spécialité choisie, "
            "sans ponctuation ni explication. En cas de doute ou de symptômes "
            "vagues/généraux, réponds \"Généraliste\"."
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        texte = (response.text or "").strip()

        for specialite in SPECIALITES_CONNUES:
            if specialite.lower() in texte.lower():
                return specialite

        logger.info("Réponse Gemini hors-liste (%s) : repli sur Généraliste.", texte)
        return "Généraliste"

    except Exception as e:
        logger.error("Erreur lors de l'appel à Gemini pour l'analyse des symptômes : %s", e)
        return "Généraliste"


def enrichir_et_trier(praticiens, patient_lat=None, patient_lon=None, type_praticien='medecin'):
    """
    Ajoute à chaque praticien (Medecin ou psy_insc) sa distance au patient
    (en km, si les deux positions sont connues) et sa note moyenne / nombre d'avis,
    puis trie la liste : d'abord par distance croissante (les praticiens sans
    position connue sont placés en fin de liste), à distance égale par note décroissante.
    """
    from django.db.models import Avg, Count
    from appointments.models import Avis

    praticiens = list(praticiens)

    for p in praticiens:
        p.distance_km = haversine_km(patient_lat, patient_lon, p.latitude, p.longitude)

        if type_praticien == 'medecin':
            agg = Avis.objects.filter(medecin=p).aggregate(moy=Avg('note'), total=Count('id'))
        else:
            agg = Avis.objects.filter(psy=p).aggregate(moy=Avg('note'), total=Count('id'))

        p.note_moyenne = round(agg['moy'], 1) if agg['moy'] else None
        p.nb_avis = agg['total'] or 0

    praticiens.sort(
        key=lambda p: (
            p.distance_km if p.distance_km is not None else float('inf'),
            -(p.note_moyenne or 0),
        )
    )
    return praticiens
