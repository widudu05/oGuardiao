# Guia de Instalação e Configuração - O Guardião

Este documento descreve o processo de instalação, configuração e implantação do sistema O Guardião.

## Requisitos do Sistema

### Software
- Python 3.9+
- PostgreSQL 13+
- Git
- Servidor web (Nginx, Apache) com suporte a proxy reverso
- Supervisor ou systemd (para gerenciamento de processos)

### Hardware (Recomendado)
- CPU: 2+ cores
- RAM: 4GB+
- Armazenamento: 20GB+ (SSD recomendado)
- Conexão de rede estável

## Preparação do Ambiente

### 1. Instalação de Dependências (Ubuntu/Debian)

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar o Python e ferramentas de desenvolvimento
sudo apt install python3 python3-pip python3-dev python3-venv -y

# Instalar o PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Instalar outras dependências
sudo apt install build-essential git nginx supervisor -y
```

### 2. Configuração do PostgreSQL

```bash
# Acessar o PostgreSQL
sudo -u postgres psql

# Criar usuário e banco de dados
CREATE USER guardiao WITH PASSWORD 'senha_segura';
CREATE DATABASE guardiao_db OWNER guardiao;
ALTER USER guardiao WITH SUPERUSER;
\q

# Testar a conexão
psql -U guardiao -h localhost -d guardiao_db
```

## Instalação da Aplicação

### 1. Clonar o Repositório

```bash
# Clonar o repositório
git clone https://github.com/widudu05/oGuardiao.git
cd oGuardiao

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependências Python

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Criar arquivo .env
touch .env
```

Edite o arquivo com as seguintes variáveis:

```
# Banco de Dados
DATABASE_URL=postgresql://guardiao:senha_segura@localhost:5432/guardiao_db

# Segurança
SESSION_SECRET=chave_secreta_longa_e_aleatoria

# Configuração do Servidor
FLASK_APP=main.py
FLASK_ENV=production
PORT=5000

# Email
MAIL_SERVER=smtp.seu-provedor.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@seu-provedor.com
MAIL_PASSWORD=senha_do_email
MAIL_DEFAULT_SENDER=noreply@oguardiao.com

# AWS S3 (opcional, para armazenamento de certificados)
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=nome-do-seu-bucket
```

### 4. Inicializar o Banco de Dados

```bash
# Executar as migrações
flask db upgrade
```

### 5. Teste de Execução

```bash
# Iniciar a aplicação em modo de teste
gunicorn --bind 0.0.0.0:5000 main:app
```

Acesse `http://localhost:5000` para verificar se a aplicação está funcionando corretamente.

## Configuração para Produção

### 1. Configurar o Supervisor

Crie um arquivo de configuração para o Supervisor:

```bash
sudo nano /etc/supervisor/conf.d/guardiao.conf
```

Adicione o seguinte conteúdo:

```ini
[program:guardiao]
directory=/caminho/para/oGuardiao
command=/caminho/para/oGuardiao/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
user=www-data
environment=PATH="/caminho/para/oGuardiao/venv/bin"
stderr_logfile=/var/log/guardiao/guardiao.err.log
stdout_logfile=/var/log/guardiao/guardiao.out.log
```

Crie os diretórios de log e recarregue o Supervisor:

```bash
sudo mkdir -p /var/log/guardiao
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start guardiao
```

### 2. Configurar o Nginx

Crie um arquivo de configuração para o Nginx:

```bash
sudo nano /etc/nginx/sites-available/guardiao
```

Adicione o seguinte conteúdo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /caminho/para/oGuardiao/static;
        expires 30d;
    }
}
```

Ative a configuração e reinicie o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/guardiao /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Configurar HTTPS com Certbot (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter e configurar certificado SSL
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

## Manutenção e Backup

### Backup do Banco de Dados

Crie um script de backup (`backup.sh`):

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/caminho/para/backups"
FILENAME="guardiao_db_$DATE.sql"

# Criar backup
pg_dump -U guardiao -h localhost guardiao_db > "$BACKUP_DIR/$FILENAME"

# Compactar backup
gzip "$BACKUP_DIR/$FILENAME"

# Manter apenas os últimos 10 backups
ls -tp "$BACKUP_DIR" | grep -v '/$' | tail -n +11 | xargs -I {} rm -- "$BACKUP_DIR/{}"
```

Configure uma tarefa cron para executar o backup diariamente:

```bash
sudo crontab -e
```

Adicione a linha:

```
0 3 * * * /caminho/para/backup.sh
```

### Atualização da Aplicação

Para atualizar a aplicação:

```bash
# Entrar no diretório da aplicação
cd /caminho/para/oGuardiao

# Ativar ambiente virtual
source venv/bin/activate

# Obter as últimas alterações
git pull

# Atualizar dependências
pip install -r requirements.txt

# Aplicar migrações do banco de dados
flask db upgrade

# Reiniciar a aplicação
sudo supervisorctl restart guardiao
```

## Resolução de Problemas

### Logs da Aplicação

Para verificar os logs da aplicação:

```bash
# Logs do Supervisor
sudo tail -f /var/log/guardiao/guardiao.out.log
sudo tail -f /var/log/guardiao/guardiao.err.log

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Verificação de Status

```bash
# Status do Supervisor
sudo supervisorctl status guardiao

# Status do Nginx
sudo systemctl status nginx

# Status do PostgreSQL
sudo systemctl status postgresql
```

### Problemas Comuns

1. **Conexão recusada com o banco de dados**:
   - Verifique se o PostgreSQL está em execução: `sudo systemctl status postgresql`
   - Verifique as credenciais no arquivo `.env`
   - Verifique as permissões do banco de dados: `psql -U guardiao -h localhost -d guardiao_db`

2. **Erro 502 Bad Gateway**:
   - Verifique se a aplicação está em execução: `sudo supervisorctl status guardiao`
   - Verifique os logs da aplicação: `sudo tail -f /var/log/guardiao/guardiao.err.log`
   - Verifique a configuração do Nginx: `sudo nginx -t`

3. **Erro ao enviar emails**:
   - Verifique as configurações de email no arquivo `.env`
   - Verifique se o servidor SMTP está acessível: `telnet smtp.seu-provedor.com 587`

4. **Problemas de permissão**:
   - Verifique as permissões dos arquivos: `sudo chown -R www-data:www-data /caminho/para/oGuardiao`
   - Verifique as permissões dos diretórios de log: `sudo chmod -R 755 /var/log/guardiao`