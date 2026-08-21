# 🏔️ Pion — Platformë Turistike

Pion është një platformë moderne e ndërtuar me **Django 5.2** që lidh turistët me udhërrëfyesit lokalë në Shqipëri. Rezervo aventura autentike, menaxho turne dhe ndaj eksperienca — gjithçka në një ndërfaqe të shpejtë, të sigurt dhe të aksesueshme.

> **Statusi**: ✅ Në prodhim gati · **Versioni**: 1.0.0

---

## ✨ Karakteristikat kryesore

### Për turistët
- ✅ Regjistrim dhe identifikim i sigurt
- ✅ Shfletim, kërkim dhe filtrim turesh (lokacion, çmim, vështirësi, etj.)
- ✅ Rezervim ture me numër pjesëmarrësish dhe llogaritje automatike e vendeve
- ✅ Statuset e rezervimit në kohë reale: **në pritje → konfirmuar → përfunduar / anuluar**
- ✅ Konfirmim pjesëmarrjeje 24 orë përpara turit
- ✅ Vlerësime dhe komente me foto
- ✅ Ture të ruajtura dhe histori rezervimesh
- ✅ Profil personal (alergji, gjendje shëndetësore, preferenca)

### Për udhërrëfyesit (Guide)
- ✅ Krijim, redaktim dhe fshirje turesh
- ✅ Çmime, zbritje, programe ditore (itinerary) dhe FAQ për çdo tur
- ✅ Konfirmim / anulim / përfundim i rezervimeve
- ✅ Statistika të detajuara për çdo tur
- ✅ Profil publik (`/users/profile/@<username>/`) me certifikata
- ✅ Verifikim nga administratori me regjistër veprimesh

### Për administratorët
- ✅ Dashboard me statistika
- ✅ Moderim i udhërrëfyesve (verifikim, pezullim, log veprimesh)
- ✅ Menaxhim i mesazheve të kontaktit, FAQ-ve dhe newsletter-it
- ✅ Konfigurim i faqes (logo, rrjete sociale, terma & privatësi, etj.)

---

## 🛠️ Teknologjitë

| Teknologji | Qëllim |
|------------|--------|
| Python 3.10+ · Django 5.2 | Backend |
| PostgreSQL | Baza e të dhënave |
| django-environ | Konfigurimi përmes `.env` |
| Django REST Framework + django-filter | API dhe filtrim i avancuar |
| django-cors-headers | Menaxhimi i CORS |
| Pillow | Përpunimi i imazheve |
| Stripe SDK | Integrimi i pagesave (në zhvillim) |
| Gunicorn · Docker · Nginx | Shërbimi në prodhim |

---

## 🚀 Fillimi i shpejtë

### Kërkesat
- **Python 3.10+**
- **pip** dhe **venv**
- **PostgreSQL** (i detyrueshëm — nuk ka fallback në SQLite; `DB_USER` dhe `DB_PASSWORD` janë të kërkuara)

### Instalimi

```bash
# 1. Klono repositorin
git clone <repository-url>
cd Pion

# 2. Krijo dhe aktivizo virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalo varësitë
pip install -r requirements.txt

# 4. Konfiguro variablat e mjedisit
cp .env.example .env
#    dhe mbushe me vlerat e tua (DB_USER, DB_PASSWORD, SECRET_KEY, etj.)

# 5. Krijo bazën e të dhënave dhe ekzekuto migrimet
python manage.py migrate

# 6. Krijo superuser për admin
python manage.py createsuperuser

# 7. Ekzekuto serverin e zhvillimit
python manage.py runserver
```

Pastaj vizito:
- **Aplikacioni**: http://localhost:8000
- **Admin**: http://localhost:8000/admin

> **Shënim**: Në modalitetin e zhvillimit (`DEBUG=True`) **nuk kërkohet** `collectstatic` — `runserver` i shërben skedarët statikë automatikisht. Email-et shfaqen në console (backend console), kështu që nuk nevojiten kredenciale SMTP lokalisht.

### Konfigurimi (`.env`)

Kopjo `.env.example` në `.env` dhe plotëso vlerat. Variablat kryesore:

| Variabël | Përshkrim | Default |
|----------|-----------|---------|
| `ENVIRONMENT` | `development` ose `production` | `development` |
| `SECRET_KEY` | **Kërkohet në prodhim** (>= 50 karaktere) | — (fallback vetëm dev) |
| `ALLOWED_HOSTS` | Hostet e lejuar, të ndara me presje | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Origjinat e besuara për CSRF | `http://127.0.0.1:8000,...` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | PostgreSQL (**USER/PASSWORD të kërkuar**) | `tour_platform` / `postgres` |
| `DB_HOST` / `DB_PORT` | Host dhe porti i DB | `localhost` / `5432` |
| `EMAIL_BACKEND` | Bosh në dev → console; SMTP në prodhim | `console` (dev) |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP (Brevo) për prodhim | `smtp-relay.brevo.com` / `587` |
| `DEFAULT_FROM_EMAIL` | Adresa nga e cila dërgohen email-et | `noreply@openmap.al` |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` | Çelësat e Stripe | — |
| `LOGIN_RATE_LIMIT_MAX_ATTEMPTS` | Provat maksimale të loginit përpara bllokimit | `5` |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Dritarja kohore (sekonda) | `600` |

---

## 📁 Struktura e projektit

```
Pion/
├── manage.py                     # Komanda kryesore e Django
├── requirements.txt              # Varësitë e Python
├── Dockerfile                    # Imazh prodhimi (multi-stage, jo-root)
├── docker-entrypoint.sh          # Prit DB → migrime → collectstatic → gunicorn
├── .env.example                  # Shembull i variablave të mjedisit
│
├── tour_platform/                # Konfigurimi kryesor
│   ├── settings/
│   │   ├── base.py               # Cilësime të përbashkëta
│   │   ├── development.py        # Zhvillim (DEBUG=True, email console)
│   │   └── production.py         # Prodhimi (hardened, HTTPS, manifest statik)
│   ├── urls.py · wsgi.py · asgi.py
│   ├── security.py               # Zgjidhja e SECRET_KEY (fail-fast në prodhim)
│   └── logging_config.py         # Logging me filtër sekretesh (SensitiveDataFilter)
│
├── core/                         # Home, rreth nesh, kontakt, FAQ, newsletter, legal
│   └── models.py                 # SiteSettings, ContactMessage, NewsletterSubscription, FAQ, SocialLink
│
├── users/                        # Autentikim, role dhe profile
│   └── models.py                 # TouristProfile, GuideProfile, GuideModerationLog
│
├── tours/                        # Menaxhimi i turneve
│   └── models.py                 # Tour, TourType, TourImage, TourSchedule, TourFAQ,
│                                 # TourReview, TourReviewImage, TourHighlight, TourTag, TourStatistic
│
├── bookings/                     # Rezervimet
│   └── models.py                 # Booking, Payment, BookingReview
│
├── payments/                     # Pagesat (Stripe — në zhvillim)
│
├── templates/                    # Shabllone HTML (Albanian UI) bazuar në base.html
├── static/                       # CSS / JS / imazhe (modulare)
│
├── media/                        # (git-ignored) Shkarkimet e përdoruesve
├── staticfiles/                  # (git-ignored) Statika e mbledhur në prodhim
└── logs/                         # (git-ignored) Skedarët e log-ut në dev
```

---

## 🗄️ Modeli i të dhënave

### Modelet kryesore
- **User** — përdoruesi i integruar i Django (me profile turisti/guide)
- **TouristProfile** — detaje të turistit (alergji, shëndet, preferenca)
- **GuideProfile** — certifikata, verifikim, statistika të guide-it
- **Tour** — turi i krijuar nga guide (çmim, kapacitet, lokacion, itinerar)
- **TourType · TourImage · TourSchedule · TourFAQ · TourReview · TourHighlight · TourTag** — shtesat e turit
- **Booking** — rezervimi që lidh turistin me turin (me UUID si çelës primar)
- **Payment** — ndjek pagesën e rezervimit
- **BookingReview** — vlerësimi i turistit pas përfundimit

### Marrëdhëniet kryesore
```
User (1) ─── (1) TouristProfile
User (1) ─── (1) GuideProfile
Guide (1) ─── (∞) Tour
Tour (1) ─── (∞) TourImage / TourSchedule / TourFAQ / TourReview / TourTag
Tour (1) ─── (∞) Booking
Tourist (1) ─── (∞) Booking
Booking (1) ─── (1) Payment
Booking (1) ─── (1) BookingReview
```

### Cikli i jetës së një rezervimi
```
pending → confirmed → completed
    ↘ cancelled (nga turisti ose guide-i)
```

- Konfirmimi i pjesëmarrjes bëhet **24 orë** para turit (`BOOKING_AUTO_CONFIRM_HOURS`).
- Anulimet kanë afat 48 orë para nisjes (`BOOKING_CANCELLATION_DEADLINE`).
- Kalimet e pavlefshme të statusit bllokohen me `ALLOWED_STATUS_TRANSITIONS`.

---

## 📱 Rrugët kryesore

### Faqe publike
| Faqja | Rruga |
|-------|-------|
| Home | `/` |
| Rreth nesh | `/rreth-nesh/` |
| Kontakt | `/kontakt/` |
| Pyetje të shpeshta | `/pyetje-te-shpeshta/` |
| Kërkimi global | `/kerko/` |
| Kushte & kondicione | `/kushte-dhe-kondicion/` |
| Politika e privatësisë | `/politika-e-privatesi/` |
| Health check | `/health/` |

### Autentikim & profile
| Faqja | Rruga |
|-------|-------|
| Regjistrim | `/users/signup/` |
| Login / Logout | `/users/login/` · `/users/logout/` |
| Ndryshim / Reset fjalëkalimi | `/users/password-change/` · `/users/password-reset/` |
| Dashboard turisti | `/users/tourist/dashboard/` |
| Dashboard guide | `/users/guide/dashboard/` |
| Dashboard admin | `/users/admin/dashboard/` |
| Profil publik i guide-it | `/users/profile/@<username>/` |

### Turne
| Faqja | Rruga |
|-------|-------|
| Lista e turneve | `/tours/` |
| Kërkim i avancuar | `/tours/search/` |
| Ture të veçuara | `/tours/featured/` |
| Ture sipas lokacionit | `/tours/location/<lokacioni>/` |
| Turet e mia | `/tours/my-tours/` |
| Krijim turi | `/tours/create/` |
| Detaje turi | `/tours/<slug>/` |
| Statistika turi | `/tours/<slug>/stats/` |
| Statuset (AJAX) | `/tours/api/status/<tour_id>/` |

### Rezervime
| Faqja | Rruga |
|-------|-------|
| Rezervo tur | `/bookings/tour/<slug>/reserve/` |
| Rezervimet e mia | `/bookings/my-bookings/` |
| Detaje rezervimi | `/bookings/<uuid>/` |
| Redakto / Anulo | `/bookings/<uuid>/edit/` · `/bookings/<uuid>/cancel/` |
| Konfirmo pjesëmarrje (24h) | `/bookings/<uuid>/confirm-participation/` |
| Vlerëso | `/bookings/<uuid>/review/` |

---

## 📧 Sistemi i email-eve

Njoftimet dërgohen përmes sinjaleve (signals) të Django. Përfshinë:

- ✅ Regjistrim i ri (mire seerdhe për turistët dhe guide-t)
- ✅ Rezervim i ri → te guide-i
- ✅ Ndryshim i statusit të rezervimit → te turisti
- ✅ Pagesa e konfirmuar / e dështuar → te turisti
- ✅ Vlerësim i ri → te guide-i
- ✅ Verifikim i profilit → te guide-i
- ✅ Mesazh kontakti → te administratori (me përgjigje automatike)
- ✅ Newsletter: mirëseardhje, anulim, dërgim masiv

Konfigurimi bëhet **vetëm përmes variablave të mjedisit** (asnjë kredencial hardcoded):

```bash
EMAIL_BACKEND=           # bosh → console në dev / SMTP në prodhim
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tuaja-veri
EMAIL_HOST_PASSWORD=tuaja-password
DEFAULT_FROM_EMAIL=noreply@openmap.al
```

---

## 🔒 Siguria

- ✅ Mbrojtje **CSRF** në të gjitha format
- ✅ **SQL injection** — parandalohet nga ORM-i i Django
- ✅ **XSS** — ikja automatike e shablloneve
- ✅ Hashing i sigurt i fjalëkalimeve + validues (minimum 8 karaktere)
- ✅ Autorizim i bazuar në role (Turist / Guide / Admin)
- ✅ **Rate limiting** për login (cache; çelësi `IP + username`, mesazh gjenerik për të shmangur enumeration)
- ✅ Në prodhim: `SECURE_SSL_REDIRECT`, **HSTS**, cookie të sigurta, `X-Frame-Options: DENY`, `CONTENT-TYPE nosniff`, **CSP**
- ✅ `SECRET_KEY` **e kërkuar** në prodhim — aplikacioni dështon në mënyrë të shpejtë (fail-fast) nëse mungon
- ✅ **Logging** me `SensitiveDataFilter` — pastron fjalëkalime, token dhe sekrete nga log-et
- ✅ Kufizime madhësie ngarkimi (5 MB) dhe lloje skedarësh të lejuara
- ✅ `ATOMIC_REQUESTS=True` — çdo kërkesë bëhet në një transaksion

---

## ♿ Aksesueshmëria & Dizajni

- ✅ HTML semantik, hierarki titujsh të saktë
- ✅ Etiketa dhe përshkrime formash, navigim me tastierë
- ✅ Kontraste ngjyrash (WCAG 2.1 AA), alt text për imazhe, ARIA labels
- ✅ **Responsive**: Mobile (320px+) · Tablet (768px+) · Desktop (1024px+)
- ✅ CSS Grid & Flexbox, `clamp()` për madhësi fluide, qasje mobile-first
- 🎨 Paleta: Primary `#0ea5e9` (blu qielli) · Success `#10b981` · Warning `#f59e0b` · Danger `#ef4444` · Background `#f8fafc`
- 🔤 Font: **Inter** (fallback sistem), Font Awesome 6.6.0 (CDN)
- 🎯 Rrezet: 12px–28px · Hije: sistem i konsistueshëm elevacioni

---

## 🧪 Testimi

```bash
python manage.py test
```

Çdo aplikacion (`core`, `users`, `tours`, `bookings`, `payments`) ka skedarët e vet `tests.py` me testet e backend-it.

---

## 🚀 Deploy

### Docker (mënyra e rekomanduar)

```bash
docker build -t pion:prod .
docker run --env-file .env -p 8000:8000 pion:prod
```

`docker-entrypoint.sh` pret që baza e të dhënave të jetë gati, ekzekuton migrimet dhe `collectstatic`, pastaj nis gunicorn-in si përdorues **jo-root**.

### Arkitektura e prodhimit

```
Internet → Nginx → Gunicorn → Django → PostgreSQL
```

- **Statikë**: `collectstatic` mbledh skedarët në `staticfiles/`. Në prodhim përdoret `ManifestStaticFilesStorage` (emra me hash + `staticfiles.json`), prandaj `collectstatic` **duhet** të ekzekutohet me modalitet prodhimi:

  ```bash
  ENVIRONMENT=production python manage.py collectstatic --no-input
  ```

- **Media**: shkarkimet ruhen në `media/`. Të dyja drejtoritë janë git-ignored — në server krijohen/shkruhen në runtime.

- **Health check**: `GET /health/` kthen `200 {"status": "ok"}` kur baza është e shëndetshme, përndryshe `503`. Drejtoje monitorimin/load balancer-in atje.

- **Logging**: në prodhim log-et shkojnë vetëm në **stdout** (systemd/journald i mbledh); në dev edhe në `logs/django.log`. Të gjitha handler-et pastrojnë sekretet.

Shembull i bllokut Nginx `server` (rregullo path-et sipas vendosjes suaj):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /opt/Pion/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /opt/Pion/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **Shënim**: Nuk kërkohet Nginx për zhvillim lokal — me `DEBUG=True` runserver shërben vetë statikën dhe median.

### Checklist para prodhimit
1. `ENVIRONMENT=production` dhe `SECRET_KEY` e fortë e vendosur
2. `ALLOWED_HOSTS` dhe `CSRF_TRUSTED_ORIGINS` të sakta
3. Kredenciale SMTP të konfiguruara
4. HTTPS/SSL aktive (HSTS dhe cookie të sigurta)
5. `collectstatic` me modalitet prodhimi
6. Monitorim përmes `/health/`

---

## 🐛 Zgjidhja e problemeve

| Problemi | Zgjidhja |
|----------|----------|
| **Statika nuk ngarkohet** | Në prodhim: `ENVIRONMENT=production python manage.py collectstatic --no-input` |
| **Gabime DB** | Verifiko `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`) dhe ekzekuto `migrate` |
| **Email-et nuk dërgohen** | Në dev shiko console; në prodhim verifiko `EMAIL_*` në `.env` |
| **Gabime 404 në shabllone** | Verifiko cilësimet `TEMPLATES` |
| **Imazhet nuk shfaqen** | Verifiko `MEDIA_URL` / `MEDIA_ROOT` dhe që media ekziston në server |
| **Login-i bllokohet** | Prit deri sa të kalojë `LOGIN_RATE_LIMIT_WINDOW_SECONDS` ose rrit kufirin në `.env` |

---

## 🔮 Rruga përpara

### Në zhvillim
- ✅ Integrimi i plotë i **Stripe** (payments app + çelësat në `.env` tashmë të gatshëm)

### Faza e ardhshme
- Njoftime në kohë reale (WebSocket) me **Celery + Redis**
- Kërkim i avancuar me Elasticsearch
- Sistemi i verifikimit të guide-ve me dokumente
- Aplikacion celular (React Native)
- Rekomandime me AI dhe dashboard analitikash
- Shumë-gjuhësh dhe shumë-valutor

---

## 📄 Licenca

Ky projekt shpërndahet nën licencën **MIT** — shih skedarin LICENSE.

---

## 🙏 Teknologjitë e përdorura

- Django framework
- PostgreSQL
- Font Awesome ikona
- Inter font
- Docker & Gunicorn & Nginx

---

**Gati për të eksploruar aventura autentike në Shqipëri!** 🏔️
