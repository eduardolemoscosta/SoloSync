# Implantação do SoloSync no Google Cloud

Este roteiro prepara uma VM Ubuntu no Compute Engine (recomendação: e2-small, região us-central1, disco persistente de 20 GB). O SQLite permanece no projeto e deve ficar em disco persistente montado em `/srv/solosync`.

## 1. Preparar Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx
sudo mkdir -p /srv/solosync/data /srv/solosync/media /srv/solosync/backups
sudo chown -R $USER:$USER /srv/solosync
```

## 2. Clonar e preparar Python

```bash
cd /srv/solosync
git clone URL_DO_REPOSITORIO app
cd app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Instale uma versão compatível com Django 6.1. Recomendado Python 3.13 no Ubuntu 24.04 ou outra instalação moderna suportada pelo Django.

## 3. Variáveis de ambiente

```bash
cp .env.example .env
chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Edite `/srv/solosync/app/.env` e configure `SECRET_KEY`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` sem aspas desnecessárias:

```env
DEBUG=False
SECRET_KEY=CHAVE_GERADA_NO_COMANDO_ACIMA
ALLOWED_HOSTS=IP_PUBLICO,DOMINIO
CSRF_TRUSTED_ORIGINS=https://DOMINIO
SECURE_SSL_REDIRECT=True
SQLITE_PATH=/srv/solosync/data/db.sqlite3
MEDIA_ROOT=/srv/solosync/media
```

Nunca publique `.env` ou credenciais reais.

## 4. Banco, estáticos e administrador

```bash
cd /srv/solosync/app
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py check --deploy
```

O banco inicial pode ser copiado uma única vez para `/srv/solosync/data/db.sqlite3`, caso o projeto já contenha dados locais:

```bash
cp /srv/solosync/app/db.sqlite3 /srv/solosync/data/db.sqlite3
python manage.py migrate
```

Faça uma cópia anterior antes de migrar ou atualizar uma instalação existente.

## 5. Gunicorn como serviço

Crie `/etc/systemd/system/solosync.service`:

```ini
[Unit]
Description=Gunicorn SoloSync
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/solosync/app
EnvironmentFile=/srv/solosync/app/.env
ExecStart=/srv/solosync/app/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
```

Antes disso, ajuste propriedade dos diretórios para `www-data` ou execute a aplicação como o usuário proprietário. Em seguida:

```bash
sudo mkdir -p /srv/solosync/data /srv/solosync/media
sudo chown -R www-data:www-data /srv/solosync/data /srv/solosync/media
sudo systemctl daemon-reload
sudo systemctl enable solosync
sudo systemctl start solosync
sudo systemctl status solosync
```

## 6. Nginx

Crie `/etc/nginx/sites-available/solosync`:

```nginx
server {
    listen 80;
    server_name DOMINIO IP_PUBLICO;

    client_max_body_size 25M;

    location /static/ {
        alias /srv/solosync/app/staticfiles/;
    }

    location /media/ {
        alias /srv/solosync/media/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Ative:

```bash
sudo ln -s /etc/nginx/sites-available/solosync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. HTTPS

Com DNS apontando para o IP público e portas 80/443 liberadas:

```bash
sudo certbot --nginx -d DOMINIO
sudo systemctl status certbot.timer
```

O certificado será renovado automaticamente pelo timer do Certbot.

## 8. Disco persistente e backups

Mantenha `/srv/solosync/data/db.sqlite3` no disco persistente da VM. Para backup consistente:

```bash
sqlite3 /srv/solosync/data/db.sqlite3 ".backup '/srv/solosync/backups/db-$(date +%F-%H%M).sqlite3'"
```

Agende cópias diárias com `cron` e copie os arquivos para armazenamento externo periodicamente. Não substitua o banco enquanto a aplicação estiver gravando sem uma cópia consistente.

## 9. Atualização

```bash
cd /srv/solosync/app
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart solosync
sudo systemctl restart nginx
```
