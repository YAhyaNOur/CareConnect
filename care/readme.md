# CareConnect 🩺

**Care** est une plateforme web (Django) de mise en relation entre patients et praticiens de santé (médecins et psychologues), avec prise de rendez-vous en ligne, recherche intelligente de praticien par symptômes (IA Gemini) et géolocalisation.

## ✨ Fonctionnalités

### Patient
- Inscription / connexion avec vérification par e-mail (code de vérification)
- Recherche de praticiens à partir des symptômes décrits (analyse via l'API Gemini) pour suggérer la spécialité adaptée
- Tri des praticiens par proximité (distance GPS, formule de Haversine)
- Prise de rendez-vous (au cabinet ou en téléconsultation)
- Suivi de ses rendez-vous, demandes de report
- Dépôt d'un avis (note + commentaire) après une consultation
- Espace compte personnel

### Médecin
- Inscription / connexion avec vérification par e-mail
- Tableau de bord : calendrier, statistiques, rendez-vous du jour
- Gestion des rendez-vous (créer, modifier, supprimer, confirmer/refuser)
- Fiche patient (symptômes, diagnostic, notes, ordonnance)
- Demande / réponse aux propositions de report de rendez-vous
- Notifications par e-mail
- Profil et localisation du cabinet

### Psychologue
- Mêmes fonctionnalités que le médecin (inscription, dashboard, RDV, profil)
- Upload de documents justificatifs à l'inscription

## 🛠️ Stack technique

- **Backend** : Django 5.2
- **Base de données** : SQLite (par défaut)
- **IA** : Google Generative AI (Gemini) — analyse des symptômes pour orienter vers la bonne spécialité
- **Traitement d'images** : Pillow
- **Visioconférence** : Jitsi Meet (instance publique `meet.jit.si`) — pour les téléconsultations
- **Frontend** : Templates Django (HTML/CSS/JS)

### 🎥 Télévisite (Jitsi Meet)

Les rendez-vous de type *téléconsultation* utilisent [Jitsi Meet](https://meet.jit.si), une solution de visioconférence gratuite et sans compte à créer :

- Chaque rendez-vous génère une room unique : `https://meet.jit.si/CareConnect-RDV-<id_du_rdv>`
- Patient et praticien rejoignent automatiquement la même room grâce à l'ID du rendez-vous
- Le bouton « Rejoindre la télévisite » n'est visible que si le RDV est **confirmé** et que l'heure actuelle se situe entre **10 minutes avant** et **60 minutes après** l'heure prévue
- ⚠️ Le lien est prévisible (basé sur l'ID du RDV) et l'instance publique de Jitsi ne demande pas d'authentification — à sécuriser (ex. token aléatoire par RDV) avant tout usage en production avec des données de santé réelles.

## 📁 Structure du projet

```
care/
├── config/          # Paramètres du projet Django (settings, urls, wsgi/asgi)
├── users/           # Comptes patients, médecins, psychologues (inscription, auth, profils)
├── appointments/    # Gestion des rendez-vous, avis, e-mails
├── recherche/       # Recherche de praticiens (IA + géolocalisation)
├── fichiers/        # Fichiers uploadés (justificatifs psy, etc.)
├── manage.py
└── requirements.txt
```

## ⚙️ Installation

1. **Cloner le projet et se placer dans le dossier**
   ```bash
   git clone <url-du-repo>
   cd care
   ```

2. **Créer un environnement virtuel et l'activer**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux / Mac
   source .venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**

   Créer un fichier `.env` à la racine du dossier `care/` avec :
   ```
   GEMINI_API_KEY=votre_clé_api_gemini
   ```

5. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

6. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```

   L'application est accessible sur `http://127.0.0.1:8000/`

## 🔑 Variables d'environnement

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API pour l'analyse des symptômes via Google Gemini |

## 👤 Auteur

Projet réalisé par **Nour** — 4ᵉ année Data Science & AI Engineering, TEK-UP University.
