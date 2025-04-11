import os
import pyotp
import qrcode
import base64
import io
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from flask import current_app, flash, url_for, render_template
from flask_mail import Message
from app import db, mail
from models import AuditLog, Certificate

def generate_mfa_secret():
    """Generate a new MFA secret for a user"""
    return pyotp.random_base32()

def generate_mfa_qr_code(user_email, secret):
    """Generate a QR code for MFA setup"""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user_email, issuer_name="O Guardião")
    
    # Create QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = io.BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

def verify_mfa_code(secret, code):
    """Verify a MFA code against a secret"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def log_audit_event(user_id, action, details=None, ip_address=None):
    """Log an audit event"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.session.add(audit_log)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to save audit log: {str(e)}")
        db.session.rollback()

def encrypt_certificate_password(password):
    """Encrypt a certificate password using AES-256"""
    # Get encryption key from environment
    key = os.environ.get("CERTIFICATE_ENCRYPTION_KEY")
    if not key:
        # Generate a random key if not set (not recommended for production)
        key = os.urandom(32)
    elif isinstance(key, str):
        # Convert string key to bytes, using padding if needed
        key = key.encode('utf-8')
        if len(key) < 32:
            key = key.ljust(32, b'\0')
        elif len(key) > 32:
            key = key[:32]
    
    # Generate a random IV
    iv = os.urandom(16)
    
    # Create an encryptor
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    
    # Pad the password
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(password.encode('utf-8')) + padder.finalize()
    
    # Encrypt the password
    encrypted_password = encryptor.update(padded_data) + encryptor.finalize()
    
    return encrypted_password, iv

def decrypt_certificate_password(encrypted_password, iv):
    """Decrypt a certificate password"""
    # Get encryption key from environment
    key = os.environ.get("CERTIFICATE_ENCRYPTION_KEY")
    if not key:
        current_app.logger.error("Encryption key not found in environment")
        return None
    elif isinstance(key, str):
        # Convert string key to bytes, using padding if needed
        key = key.encode('utf-8')
        if len(key) < 32:
            key = key.ljust(32, b'\0')
        elif len(key) > 32:
            key = key[:32]
    
    # Create a decryptor
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    
    # Decrypt the password
    decrypted_padded = decryptor.update(encrypted_password) + decryptor.finalize()
    
    # Unpad the result
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    try:
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
        return decrypted_data.decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Failed to decrypt password: {str(e)}")
        return None

def send_invitation_email(invite):
    """Send an invitation email to a new user"""
    try:
        accept_url = url_for('accept_invite', token=invite.token, _external=True)
        
        msg = Message(
            subject="Convite para O Guardião",
            recipients=[invite.email],
            html=render_template('emails/invite.html', 
                                invite=invite, 
                                accept_url=accept_url)
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send invitation email: {str(e)}")
        return False

def send_expiration_alert(certificate, days_left):
    """Send certificate expiration alert email"""
    try:
        # Get admin users for the organization
        from models import User
        admins = User.query.filter_by(
            organization_id=certificate.company.organization_id,
            role__in=['admin', 'master_admin']
        ).all()
        
        if not admins:
            current_app.logger.warning(f"No admins found for certificate {certificate.id} alert")
            return False
        
        recipients = [admin.email for admin in admins]
        
        msg = Message(
            subject=f"ALERTA: Certificado expirando em {days_left} dias",
            recipients=recipients,
            html=render_template('emails/certificate_expiration.html', 
                                certificate=certificate, 
                                days_left=days_left)
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send expiration alert: {str(e)}")
        return False

def check_expiring_certificates():
    """Check for certificates that are expiring soon and send alerts"""
    today = datetime.now().date()
    
    # Check for certificates expiring in 30, 15, and 5 days
    alert_days = [30, 15, 5]
    
    for days in alert_days:
        expiry_date = today + timedelta(days=days)
        certificates = Certificate.query.filter_by(expiry_date=expiry_date).all()
        
        for cert in certificates:
            send_expiration_alert(cert, days)
            
    # Return count of certificates expiring in next 30 days (for dashboard)
    return Certificate.query.filter(
        Certificate.expiry_date <= today + timedelta(days=30),
        Certificate.expiry_date > today
    ).count()
