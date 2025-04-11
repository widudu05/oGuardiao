from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app import db
from forms import LoginForm, RegistrationForm, MFAForm, ConviteForm, RegisterFromInviteForm, SetupMFAForm
from models import Usuario, Organizacao, ConviteUsuario
from utils import generate_mfa_secret, generate_mfa_qr_code, verify_mfa_code, log_audit
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        if user and user.verify_password(form.password.data):
            if not user.ativo:
                flash('Sua conta está desativada. Entre em contato com o administrador.', 'danger')
                return render_template('login.html', form=form)
            
            # If MFA is enabled, redirect to MFA verification
            if user.mfa_enabled:
                session['user_id'] = user.id
                session['remember_me'] = form.remember_me.data
                return redirect(url_for('auth.verify_mfa'))
            
            # Log user in
            login_user(user, remember=form.remember_me.data)
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            
            log_audit(user.id, 'Login', 'Login bem-sucedido')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        
        flash('Email ou senha inválidos.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    form = MFAForm()
    
    if form.validate_on_submit():
        user = Usuario.query.get(session['user_id'])
        
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('auth.login'))
        
        if verify_mfa_code(user.mfa_secret, form.code.data):
            login_user(user, remember=session.get('remember_me', False))
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            
            log_audit(user.id, 'Login MFA', 'Login com autenticação de dois fatores')
            
            # Clear session data
            session.pop('user_id', None)
            session.pop('remember_me', None)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        
        flash('Código MFA inválido. Tente novamente.', 'danger')
    
    return render_template('auth/verify_mfa.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'Logout', 'Logout bem-sucedido')
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create organization
        org = Organizacao(
            nome=form.nome_organizacao.data,
            cnpj=form.cnpj.data,
            email_contato=form.email.data
        )
        db.session.add(org)
        db.session.flush()  # Get the org ID
        
        # Create user as admin
        user = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            tipo='admin',
            organizacao_id=org.id
        )
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        
        flash('Registro concluído! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/convite/<token>', methods=['GET', 'POST'])
def register_from_invite(token):
    # Find the invitation
    convite = ConviteUsuario.query.filter_by(token=token).first()
    
    if not convite or convite.usado or convite.expirado():
        flash('Convite inválido ou expirado.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = RegisterFromInviteForm()
    if form.validate_on_submit():
        # Create user
        user = Usuario(
            nome=form.nome.data,
            email=convite.email,
            tipo=convite.tipo_usuario,
            organizacao_id=convite.organizacao_id
        )
        user.password = form.password.data
        
        # Mark invitation as used
        convite.usado = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registro concluído! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
    
    form.token.data = token
    return render_template('auth/register_from_invite.html', form=form, email=convite.email)

@auth_bp.route('/profile/mfa-setup', methods=['GET', 'POST'])
@login_required
def mfa_setup():
    if current_user.mfa_enabled:
        flash('MFA já está ativado para sua conta.', 'info')
        return redirect(url_for('profile'))
    
    form = SetupMFAForm()
    
    if request.method == 'GET':
        # Generate a new secret
        secret = generate_mfa_secret()
        qr_code = generate_mfa_qr_code(current_user.email, secret)
        form.secret.data = secret
        return render_template('profile/mfa.html', form=form, qr_code=qr_code, secret=secret)
    
    if form.validate_on_submit():
        # Verify the code
        if verify_mfa_code(form.secret.data, form.code.data):
            # Enable MFA
            current_user.mfa_enabled = True
            current_user.mfa_secret = form.secret.data
            db.session.commit()
            
            log_audit(current_user.id, 'MFA Ativado', 'Autenticação de dois fatores ativada')
            
            flash('Autenticação de dois fatores ativada com sucesso!', 'success')
            return redirect(url_for('profile'))
        
        flash('Código inválido. Tente novamente.', 'danger')
        # Re-generate QR code
        qr_code = generate_mfa_qr_code(current_user.email, form.secret.data)
        return render_template('profile/mfa.html', form=form, qr_code=qr_code, secret=form.secret.data)
    
    return render_template('profile/mfa.html', form=form)

@auth_bp.route('/profile/mfa-disable', methods=['POST'])
@login_required
def mfa_disable():
    if not current_user.mfa_enabled:
        flash('MFA não está ativado para sua conta.', 'info')
        return redirect(url_for('profile'))
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.session.commit()
    
    log_audit(current_user.id, 'MFA Desativado', 'Autenticação de dois fatores desativada')
    
    flash('Autenticação de dois fatores desativada com sucesso!', 'success')
    return redirect(url_for('profile'))
