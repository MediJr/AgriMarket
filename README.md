# AgriMarket

Plateforme de **mise en relation agricole** entre producteurs, fournisseurs et acheteurs en RDC.

Le cœur métier : publication d'offres et de demandes, matching intelligent, commandes et notifications. L'observatoire des prix fournit un **contexte de décision** (prix de référence), sans être le hub principal.

## Stack

- Django 5+
- Django REST Framework + Simple JWT
- MySQL 8 (Docker) / SQLite (local rapide)
- Redis 7 (optionnel en dev)
- Bootstrap 5

## Architecture

```
apps/accounts/      → Utilisateurs, profils, rôles
apps/catalog/       → Catégories, produits (+ API price-context)
apps/marketplace/   → Offres, demandes, commandes, matching (cœur métier)
apps/prices/        → Marchés, relevés (service de contexte)
apps/notifications/ → Notifications in-app
```

## Installation locale

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Pour un démarrage rapide sans Docker, dans `.env` :

```
DATABASE_URL=sqlite:///db.sqlite3
USE_REDIS=False
```

```bash
py manage.py migrate
py manage.py load_demo_data
py manage.py runserver
```

Application : http://127.0.0.1:8001


Comptes démo (mot de passe `demo1234`) :
- `demo_producer` — producteur
- `demo_supplier` — fournisseur
- `demo_buyer` — acheteur

## Docker

```bash
cp .env.example .env
Avec Docker : docker compose up --build
Puis ouvrir : http://127.0.0.1:8001
```

Puis :

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py load_demo_data
docker compose exec web python manage.py createsuperuser
```

## Parcours utilisateur (MVP)

1. **Inscription** — `/register/` ou `POST /api/auth/register/`
2. **Connexion** — `/login/` ou `POST /api/auth/token/`
3. **Publication** — offre (producteur/fournisseur) ou demande (acheteur)
4. **Matching** — suggestions sur fiches détail et via API
5. **Commande** — depuis fiche offre ou API
6. **Gestion** — vendeur accepte/refuse/termine (`/my/offers/`)
7. **Notifications** — automatiques à chaque étape clé
8. **Prix de référence** — bandeau contextuel + `/observatory/`

## API principale

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register/` | Inscription |
| POST | `/api/auth/token/` | JWT (username + password) |
| POST | `/api/auth/token/refresh/` | Refresh token |
| GET | `/api/products/` | Catalogue |
| GET | `/api/products/{id}/price-context/?province=...` | Contexte prix validés |
| GET/POST | `/api/offers/` | Offres |
| GET | `/api/offers/{id}/matching-requests/` | Demandes compatibles |
| GET/POST | `/api/purchase-requests/` | Demandes d'achat |
| GET | `/api/purchase-requests/{id}/matching-offers/` | Offres compatibles |
| GET/POST | `/api/orders/` | Commandes |
| POST | `/api/orders/{id}/accept/` | Accepter (vendeur) |
| POST | `/api/orders/{id}/reject/` | Refuser (vendeur) |
| POST | `/api/orders/{id}/complete/` | Terminer (vendeur) |
| GET | `/api/notifications/` | Notifications utilisateur |

## Pages web

| URL | Description |
|-----|-------------|
| `/` | Accueil |
| `/offers/` | Liste des offres |
| `/offers/create/` | Publier une offre |
| `/requests/` | Liste des demandes |
| `/requests/create/` | Publier une demande |
| `/my/offers/` | Espace vendeur |
| `/my/requests/` | Mes demandes |
| `/my/orders/` | Mes commandes |
| `/my/notifications/` | Notifications utilisateur |

## Tests

```bash
py manage.py check
py manage.py test
```

## Configuration

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Clé secrète |
| `DATABASE_URL` | URL base de données |
| `USE_REDIS` | `True`/`False` — cache Redis ou LocMem |
| `REDIS_URL` | URL Redis si activé |

JWT : access token 1 h, refresh token 7 jours (`SIMPLE_JWT` dans settings).

## Après MVP (v1.0)

- Mobile Money et paiement en ligne
- Logistique transporteur
- KYC avancé et modération
- Messagerie entre acteurs
- Cartographie et statistiques avancées
