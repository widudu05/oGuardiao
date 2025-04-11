from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import logging
import pyotp
import qrcode
from io import BytesIO
import base64
from models import Alerta, Certificado, LogAuditoria
from app import db, app
from flask import request

logger = logging.getLogger(__name__)

def encrypt_certificate_password(password, key=None):
    """
    Encrypt certificate password using AES-256
    Returns encrypted password and IV
    """
    if key is None:
        key = app.config.get('SECRET_KEY', os.urandom(32))[:32].encode()
    else:
        key = key.encode()
        
    # Ensure key is 32 bytes (256 bits)
    if len(key) < 32:
        key = key.ljust(32, b'\0')
    elif len(key) > 32:
        key = key[:32]
    
    # Generate a random 16-byte initialization vector
    iv = os.urandom(16)
    
    # Create an encryptor
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Pad the plaintext to a multiple of 16 bytes
    padded_password = password.encode()
    padding_length = 16 - (len(padded_password) % 16)
    padded_password += bytes([padding_length]) * padding_length
    
    # Encrypt the padded plaintext
    ciphertext = encryptor.update(padded_password) + encryptor.finalize()
    
    # Return base64 encoded ciphertext and IV
    return base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode()

def decrypt_certificate_password(encrypted_password, iv, key=None):
    """
    Decrypt certificate password
    """
    if key is None:
        key = app.config.get('SECRET_KEY', '').encode()[:32]
    else:
        key = key.encode()
        
    # Ensure key is 32 bytes (256 bits)
    if len(key) < 32:
        key = key.ljust(32, b'\0')
    elif len(key) > 32:
        key = key[:32]
    
    # Decode the base64 encoded ciphertext and IV
    ciphertext = base64.b64decode(encrypted_password)
    iv = base64.b64decode(iv)
    
    # Create a decryptor
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Decrypt the ciphertext
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove the padding
    padding_length = padded_plaintext[-1]
    plaintext = padded_plaintext[:-padding_length]
    
    return plaintext.decode()

def upload_certificate_to_s3(file, file_name, bucket=None):
    """
    Upload certificate to S3 with AES-256 server-side encryption
    Returns the S3 object URL
    """
    if bucket is None:
        bucket = app.config.get('AWS_S3_BUCKET_NAME')
    
    # Create a boto3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=app.config.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=app.config.get('AWS_SECRET_ACCESS_KEY'),
        region_name=app.config.get('AWS_S3_REGION')
    )
    
    try:
        # Upload the file with server-side encryption
        s3_client.upload_fileobj(
            file,
            bucket,
            file_name,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'ContentType': 'application/x-pkcs12'
            }
        )
        
        # Generate a URL for the file
        url = f"s3://{bucket}/{file_name}"
        return url
    
    except ClientError as e:
        logger.error(f"Error uploading certificate to S3: {e}")
        raise

def generate_mfa_secret():
    """Generate a new MFA secret key"""
    return pyotp.random_base32()

def generate_mfa_qr_code(user_email, secret):
    """Generate QR code for MFA setup"""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user_email, issuer_name="O Guardião")
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for HTML embedding
    buffered = BytesIO()
    img.save(buffered)
    return base64.b64encode(buffered.getvalue()).decode()

def verify_mfa_code(secret, code):
    """Verify MFA code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def check_for_expiring_certificates():
    """
    Check for certificates that are about to expire and create alerts
    """
    today = datetime.utcnow().date()
    
    # Check for certificates expiring in 30, 15, and 5 days
    alert_days = [30, 15, 5]
    
    for days in alert_days:
        target_date = today + timedelta(days=days)
        
        # Find certificates that expire on the target date and don't have an alert yet
        expiring_certs = Certificado.query.filter(
            Certificado.data_vencimento.between(
                datetime.combine(target_date, datetime.min.time()),
                datetime.combine(target_date, datetime.max.time())
            )
        ).all()
        
        for cert in expiring_certs:
            # Check if an alert already exists for this certificate and days
            existing_alert = Alerta.query.filter_by(
                certificado_id=cert.id,
                dias_restantes=days
            ).first()
            
            if not existing_alert:
                # Create a new alert
                alert = Alerta(
                    certificado_id=cert.id,
                    dias_restantes=days
                )
                db.session.add(alert)
    
    db.session.commit()

def log_audit(user_id, action, description=None):
    """
    Log an audit entry
    """
    log = LogAuditoria(
        usuario_id=user_id,
        acao=action,
        descricao=description,
        endereco_ip=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
