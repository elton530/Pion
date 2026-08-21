# Plani i plotë i deploy-imit — Pion (Django + PostgreSQL) · Azure Free Tier

> Udhëzues hap pas hapi për të nisur **Pion** në një VM falas Azure
> (faza e testimit/demos), me rrugën e migrimit në pagesë kur projekti rritet.
> Të gjitha rrugët e skedarëve dhe emrat e moduleve janë përshtatur me
> repozitorin aktual `github.com/elton530/Pion`.

## 1. Përmbledhje e komponentëve

| Komponenti | Shërbimi | Kosto | Rol |
|---|---|---|---|
| Compute (server) | Azure VM (B1s) | Falas (750 orë/muaj) | Ekzekuton Django, Nginx, Gunicorn |
| Databaza | PostgreSQL (vetë-instaluar në VM) | Falas | Ruajtja e të dhënave |
| Web server | Nginx | Falas (open source) | Reverse proxy, servon static/media |
| App server | Gunicorn | Falas (open source) | Ekzekuton Django (WSGI) |
| Domain | Namecheap `.me` | Falas 1 vit | Adresa publike e projektit |
| SSL/HTTPS | Let's Encrypt (Certbot) | Falas, i përhershëm | Kripto e trafikut |
| Email (SMTP) | Brevo | Falas (300/ditë) | Dërgim email (regjistrim, njoftime) |
| Kodi | GitHub (`elton530/Pion`) | Falas | Ruajtja e kodit, deploy |
| Monitorim | UptimeRobot (`/health/`) | Falas | Kontroll disponueshmërie |
| Backup databaze | Script bash + cron | Falas | Siguri e të dhënave |

**Parimi kryesor:** çdo komponent zgjidhet të mos konsumojë kredit financiar —
VM-ja përdor orët falas, PostgreSQL instalohet vetë brenda VM-së, SSL/email
janë falas nga natyra e shërbimit.

---

## 2. Arkitektura (si bashkëveprojnë komponentët)

```
Përdoruesi → Domain (.me) → DNS (A record) → IP e VM Azure
                                                  │
                                            ┌─────▼─────┐
                                            │   Nginx   │  (porti 80/443, SSL,
                                            └─────┬─────┘   shërben /static/ dhe /media/)
                                                  │ proxy_pass
                                            ┌─────▼─────┐
                                            │  Gunicorn │  (WSGI, socket lokal)
                                            └─────┬─────┘
                                                  │
                                            ┌─────▼─────┐
                                            │   Django  │  (moduli: tour_platform)
                                            └─────┬─────┘
                                          ┌────────┴────────┐
                                    ┌─────▼─────┐    ┌──────▼──────┐
                                    │ PostgreSQL│    │ Brevo (SMTP)│
                                    └───────────┘    └─────────────┘
```

> **Shenim mbi projektin:** Pion-i përdor `django-environ` — konfigurimi bëhet
> **vetëm** përmes skedarit `.env`, **jo** duke ndryshuar `settings.py`.
> Për prodhim vendos `ENVIRONMENT=production` (aktivizon `DEBUG=False`,
> hardening, manifest statik me hash). Pa këtë, aplikacioni niset në modalitet
> zhvillimi dhe statika në prodhim nuk do të funksionojë.

---

## 3. Hapat e plotë, në rend

### Hapi 1 — Krijo llogarinë Azure for Students
1. Shko te `azure.microsoft.com/free/students`
2. Regjistrohu me email-in tënd universitar (s'kërkohet kartë krediti)
3. Verifikohu përmes GitHub Student Pack nëse kërkohet
4. Konfirmo që ke $100 kredit dhe akses te shërbimet "Always Free"

### Hapi 2 — Regjistro domain-in te Namecheap
1. Nga paneli GitHub Student Pack, hap ofertën Namecheap
2. Autorizo lidhjen me GitHub
3. Kërko domain-in tënd `.me` dhe regjistroje (do të jetë $0)
4. **Menjëherë pas regjistrimit**: Namecheap Dashboard → çaktivizo Auto-Renew

### Hapi 3 — Krijo Virtual Machine në Azure
1. Portali Azure → **Create Resource → Virtual Machine**
2. Zgjidh: **Ubuntu Server 22.04 LTS**
3. Madhësia: **B1s** (brenda tier-it falas)
4. Krijo/ngarko një **SSH key pair** (jo password)
5. Në Network Security Group hap vetëm portet: **22 (SSH), 80 (HTTP), 443 (HTTPS)**
6. Ruaj **IP-në publike statike** (kërkohet për rekordin DNS)

### Hapi 4 — Lidhu me VM-në dhe përgatit serverin
```bash
ssh -i /path/to/key.pem azureuser@IP_E_VM
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx postgresql \
    postgresql-contrib git ufw
```

Aktivizo firewall-in (pa këtë, HTTP/HTTPS s'do të arrijnë te VM):
```bash
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
sudo ufw enable && sudo ufw status
```

### Hapi 5 — Konfiguro PostgreSQL
Krijo bazën dhe përdoruesin me emra që do t'i vendosësh edhe në `.env`
(më poshtë përdoren vlerat default të projektit `tour_platform`):
```bash
sudo -u postgres psql
CREATE DATABASE tour_platform ENCODING 'UTF8' TEMPLATE template0;
CREATE USER pion_user WITH PASSWORD 'fjalëkalim_i_fortë';
GRANT ALL PRIVILEGES ON DATABASE tour_platform TO pion_user;
ALTER ROLE pion_user SET client_encoding TO 'utf8';
ALTER ROLE pion_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE pion_user SET timezone TO 'UTC';
\q
```

### Hapi 6 — Klono projektin dhe konfiguro `.env` (jo settings.py!)
```bash
cd /home/azureuser
git clone https://github.com/elton530/Pion.git
cd Pion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt    # përfshin gunicorn e psycopg2-binary
```

Kopjo dhe plotëso skedarin e konfigurimit:
```bash
cp .env.example .env
nano .env
```

Vlerat që duhen në prodhim (emrat përputhen me hapin 5):

| Variabël | Vlera |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | gjenero: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | `domainimyt.me,www.domainimyt.me` (pas hapit 9 shto IP-në nëse duhet) |
| `CSRF_TRUSTED_ORIGINS` | `https://domainimyt.me,https://www.domainimyt.me` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | `tour_platform` / `pion_user` / fjalëkalimi |
| `DB_HOST` / `DB_PORT` | `localhost` / `5432` |
| `EMAIL_*` + `DEFAULT_FROM_EMAIL` | kredencialet e Brevo-s (hapi 11) |
| `STRIPE_*` | çelësat live (ose lëri bosh sa nuk janë aktive) |

> **Kritike:** `DB_USER` dhe `DB_PASSWORD` **janë të detyrueshëm** — aplikacioni
> dështon (fail-fast) nëse mungojnë. Kurrë mos i ruaj në repo (`.env` është në
> `.gitignore`).

Migro, mblidh statikën dhe krijo admin:
```bash
python manage.py migrate
ENVIRONMENT=production python manage.py collectstatic --noinput
python manage.py createsuperuser
```

> `collectstatic` **duhet** të ekzekutohet me `ENVIRONMENT=production` sepse
> vetëm atëherë gjenerohet manifest-i me emra të hash-uar (`staticfiles.json`).
> Rezultati ruhet në `staticfiles/` — pikërisht aty do ta drejtojë Nginx.

### Hapi 7 — Konfiguro Gunicorn si shërbim (systemd)
Krijo `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=Gunicorn daemon for Pion (Django)
After=network.target postgresql.service

[Service]
User=azureuser
Group=www-data
WorkingDirectory=/home/azureuser/Pion
EnvironmentFile=/home/azureuser/Pion/.env
ExecStart=/home/azureuser/Pion/venv/bin/gunicorn tour_platform.wsgi:application \
    --workers 3 --bind unix:/home/azureuser/Pion/pion.sock
Restart=always

# Log-et shkojnë në journald: journalctl -u gunicorn -f
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
```bash
# Nginx (www-data) duhet të arrijë socket-in → jep të drejta në dosjen e shtëpisë
sudo chmod 755 /home/azureuser
sudo chown -R azureuser:www-data /home/azureuser/Pion/{staticfiles,media,logs}
sudo systemctl daemon-reload
sudo systemctl start gunicorn && sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

> **Shenim:** moduli WSGI i projektit është `tour_platform.wsgi:application`
> (jo `projekti.wsgi`). `EnvironmentFile` siguron që `ENVIRONMENT=production`
> e të tjerat ngarkohen në mjedisin e shërbimit.

### Hapi 8 — Konfiguro Nginx
Krijo `/etc/nginx/sites-available/pion`:
```nginx
server {
    listen 80;
    server_name domainimyt.me www.domainimyt.me;

    # Statika e mbledhur nga collectstatic (Nginx e shërben, Django kurrë)
    location /static/ {
        alias /home/azureuser/Pion/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Imazhet e ngarkuara nga përdoruesit
    location /media/ {
        alias /home/azureuser/Pion/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Kufiri i ngarkimit të imazheve (projekti lejon deri 5 MB)
    client_max_body_size 6m;

    location = /favicon.ico { access_log off; log_not_found off; }

    location / {
        proxy_pass http://unix:/home/azureuser/Pion/pion.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/pion /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

> **Kritike:** header-i `X-Forwarded-Proto` është i detyrueshëm — prodhimi
> (`production.py`) e përdor përmes `SECURE_PROXY_SSL_HEADER` për të dalluar
> HTTPS nga HTTP (SSL redirect, cookie të sigurta).

### Hapi 9 — Lidh domain-in (DNS)
Te paneli Namecheap → **Advanced DNS**:
- Shto **A Record**: Host `@`, Value = IP e VM-së
- Shto **A Record**: Host `www`, Value = IP e VM-së
- Prit propagimin (15 min – 24 orë)

Verifiko: `dig +short domainimyt.me` duhet të kthejë IP-në e VM-së.

### Hapi 10 — Aktivizo HTTPS (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d domainimyt.me -d www.domainimyt.me
sudo certbot renew --dry-run    # rinovimi automatik konfigurohet vetë
```

Pas kësaj verifiko që:
- `curl -I https://domainimyt.me` → `200 OK`
- `curl -I http://domainimyt.me` → redirect 301 në HTTPS (nga `SECURE_SSL_REDIRECT`)

### Hapi 11 — Konfiguro SMTP + DNS (SPF/DKIM/DMARC) për Brevo
1. Te Brevo: **Settings → Senders & IP → Add & verify domain** — merr rekordet
2. Te Namecheap DNS shto rekordet që të jep Brevo:
   - **DKIM**: CNAME sipas udhëzimeve të Brevo-s
   - **SPF**: `TXT` në `@` → `v=spf1 include:spf.mail.brevo.com ~all`
     (kujdes: **një** rekord SPF për domain — mos shto dublikata)
   - **DMARC** (opsionale): `TXT` në `_dmarc` → `v=DMARC1; p=quarantine; rua=mailto:you@domainimyt.me`
3. Plotëso `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `DEFAULT_FROM_EMAIL`
   në `/home/azureuser/Pion/.env` dhe rinis shërbimin: `sudo systemctl restart gunicorn`
4. Verifiko te Brevo pas propagimit dhe testo një regjistrim/reset password

### Hapi 12 — Backup automatik i databazës
Krijo `/home/azureuser/backup.sh` (passwordi lexohet nga `.pgpass`, jo i ruajtur
i pastër në script):
```bash
#!/bin/bash
mkdir -p /home/azureuser/backups
pg_dump -U pion_user -h localhost tour_platform -F c \
    -f /home/azureuser/backups/backup_$(date +%Y%m%d).dump
find /home/azureuser/backups -mtime +7 -delete
```
```bash
chmod +x /home/azureuser/backup.sh
touch ~/.pgpass && chmod 600 ~/.pgpass
echo "localhost:5432:tour_platform:pion_user:fjalëkalim_i_fortë" > ~/.pgpass
crontab -e
# Shto rreshtin (çdo natë në 2:00):
0 2 * * * /home/azureuser/backup.sh
```

Testo backup-in: `./backup.sh && ls -la ~/backups`. Për të restauruar:
```bash
pg_restore --clean --if-exists -d tour_platform ~/backups/backup_XXXX.dump
```

> Rekomandohet gjithashtu një kopje e rregullt e `media/` (p.sh. `rsync` në
> një hapësirë tjetër) — bazat e të dhënave nuk mbajnë imazhet e ngarkuara.

### Hapi 13 — Monitorim bazë
Regjistrohu falas te **UptimeRobot** dhe shto URL-në:
`https://domainimyt.me/health/`

Endpoint-i `/health/` është publik, pa autentikim: kthen `200 {"status": "ok"}`
kur DB është e shëndetshme, `503 {"status": "error"}` përndryshe — ideal për
monitorim të disponueshmërisë.

---

## 4. Checklist final para "demo gati"

- [ ] `ENVIRONMENT=production` në `.env` (jo `DEBUG=False` me dorë — kjo e çaktivizon hardening)
- [ ] Domain aktiv dhe HTTPS funksionon (kyçi i gjelbër te browser)
- [ ] Django ekzekuton përmes Gunicorn si shërbim systemd (rindizet vetë pas rinisjes së VM)
- [ ] `ALLOWED_HOSTS` dhe `CSRF_TRUSTED_ORIGINS` të sakta
- [ ] Statika shfaqet me emra të hash-uar (`/static/css/base.<hash>.css`) — shenjë se manifest-i u gjenerua
- [ ] Imazhet e media-s ngarkohen dhe shfaqen
- [ ] PostgreSQL ka backup automatik ditor (testuar)
- [ ] Email dërgohet saktë dhe nuk shkon te spam (SPF/DKIM PASS)
- [ ] `/health/` kthen 200 dhe monitorohet nga UptimeRobot
- [ ] Superuser i krijuar për panelin admin (`/admin/`)
- [ ] Firewall (ufw) hap vetëm portet 22/80/443

---

## 5. Plani i migrimit në pagesë (nëse projekti ka sukses)

1. **Kredi Azure mbaron ose VM nuk mjafton më** → upgrade VM-në në madhësi më
   të madhe (B2s, etj.) brenda së njëjtës llogari, pa migrim
2. **Trafiku rritet** → konsidero Azure Database for PostgreSQL (managed) në
   vend të vetë-instaluar; ndrysho `DB_HOST` në `.env` dhe rinis gunicorn
3. **Domain** → kalo në `.com` real (p.sh. përmes Cloudflare)
4. **Migrimi i databazës** (nëse ndryshon serveri):
   ```bash
   pg_dump -F c -f backup.dump                       # nga serveri i vjetër
   pg_restore --clean --if-exists -d tour_platform backup.dump   # te ai i ri
   ```
5. **SMTP** → mbi 300 email/ditë, upgrade plani i Brevo-s (pa ndryshim konfigurimi)
6. **Opsion pa VM** → kur rritet, një PaaS (Railway/Render/Fly.io) me `gunicorn`
   nga `requirements.txt` është më i thjeshtë për t'u mirëmbajtur

---

## 6. Zgjidhja e problemeve

| Simptomë | Shkaku i mundshëm | Zgjidhja |
|----------|-------------------|----------|
| `502 Bad Gateway` | Gunicorn i rrëzuar ose socket i gabuar | `sudo journalctl -u gunicorn -f`; verifiko `pion.sock` |
| `Bad Request (400)` | `ALLOWED_HOSTS` e pasaktë | Shto domainin në `.env` dhe rinis gunicorn |
| Statika jep `404` ose pa stil | `collectstatic` në modalitet zhvillimi | `ENVIRONMENT=production python manage.py collectstatic --noinput` |
| `{% static %}` gabon në prodhim | Manifest-i mungon | Riekkuro `collectstatic` në prodhim dhe rinis gunicorn |
| Imazhet nuk ngarkohen | Të drejta në `media/` | `chown azureuser:www-data media/` |
| Redirect loop (http→https) | `X-Forwarded-Proto` mungon | Shto `proxy_set_header X-Forwarded-Proto $scheme;` në Nginx |
| `ImproperlyConfigured: SECRET_KEY` | `SECRET_KEY` mungon në prodhim | Shtoje në `.env` |
| DB e paarritshme | Kredenciale ose `listen_addresses` | Verifiko `DB_*` në `.env`; `sudo systemctl status postgresql` |

---

*Shënim: ky plan bazohet në ofertat aktive të GitHub Student Developer Pack në
gusht 2026. DigitalOcean nuk përfshihet më (u tërhoq nga programi më 1 gusht
2026). Për detaje rreth arkitekturës së projektit shiko `README.md`.*
