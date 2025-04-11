# Dependências do Projeto

## Bibliotecas Python
- Flask==2.2.3
- Flask-Login==0.6.2
- Flask-Mail==0.9.1
- Flask-SQLAlchemy==3.0.3
- Flask-WTF==1.1.1
- gunicorn==23.0.0
- psycopg2-binary==2.9.6
- SQLAlchemy==2.0.4
- Werkzeug==2.2.3
- WTForms==3.0.1
- boto3==1.26.87
- botocore==1.29.87
- cryptography==39.0.1
- email-validator==1.3.1
- pyotp==2.8.0
- qrcode==7.4.2
- Pillow==9.4.0
- python-dotenv==1.0.0

## Requisitos do Sistema
- Python 3.9+
- PostgreSQL 13+

## Variáveis de Ambiente
```
# Banco de dados
DATABASE_URL=postgresql://user:password@localhost:5432/oguardiao

# Segurança
SESSION_SECRET=your-secret-key

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=noreply@oguardiao.com

# AWS S3 (armazenamento de certificados)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=oguardiao-certificates
```