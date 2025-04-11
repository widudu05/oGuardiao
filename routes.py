from flask import render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import logging

from app import app, db
from models import (
    Usuario, Organizacao, Empresa, Certificado, LogAuditoria, 
    ConviteUsuario, Alerta, TIPO_CERTIFICADO_CHOICES
)
from forms import (
    OrganizacaoForm, EmpresaForm, CertificadoUploadForm, 
    ConviteForm, PerfilForm
)
from utils import (
    encrypt_certificate_password, decrypt_certificate_password, 
    upload_certificate_to_s3, log_audit, check_for_expiring_certificates
)

logger = logging.getLogger(__name__)

# Dashboard route
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent certificates
    certificates = Certificado.query.join(Empresa).filter(
        Empresa.organizacao_id == current_user.organizacao_id
    ).order_by(Certificado.data_vencimento).limit(10).all()
    
    # Get count of certificates by status
    valid_count = 0
    warning_count = 0
    critical_count = 0
    expired_count = 0
    
    all_certificates = Certificado.query.join(Empresa).filter(
        Empresa.organizacao_id == current_user.organizacao_id
    ).all()
    
    for cert in all_certificates:
        status = cert.status()
        if status == "Válido":
            valid_count += 1
        elif status == "Atenção":
            warning_count += 1
        elif status in ["Alerta", "Crítico"]:
            critical_count += 1
        elif status == "Vencido":
            expired_count += 1
    
    # Get recent logs
    logs = LogAuditoria.query.filter_by(
        usuario_id=current_user.id
    ).order_by(LogAuditoria.data_hora.desc()).limit(5).all()
    
    # Get company count
    company_count = Empresa.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).count()
    
    # Get user count
    user_count = Usuario.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).count()
    
    return render_template(
        'dashboard.html', 
        certificates=certificates,
        valid_count=valid_count,
        warning_count=warning_count,
        critical_count=critical_count,
        expired_count=expired_count,
        logs=logs,
        company_count=company_count,
        user_count=user_count
    )

# Certificate routes
@app.route('/certificados')
@login_required
def certificados():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    empresa_id = request.args.get('empresa_id', type=int)
    status = request.args.get('status')
    tipo = request.args.get('tipo')
    
    # Base query
    query = Certificado.query.join(Empresa).filter(
        Empresa.organizacao_id == current_user.organizacao_id
    )
    
    # Apply filters
    if empresa_id:
        query = query.filter(Certificado.empresa_id == empresa_id)
    
    if status:
        today = datetime.utcnow().date()
        if status == 'valido':
            # More than 30 days
            thirty_days = today + timedelta(days=30)
            query = query.filter(Certificado.data_vencimento > thirty_days)
        elif status == 'atencao':
            # Between 15 and 30 days
            fifteen_days = today + timedelta(days=15)
            thirty_days = today + timedelta(days=30)
            query = query.filter(
                Certificado.data_vencimento > fifteen_days,
                Certificado.data_vencimento <= thirty_days
            )
        elif status == 'alerta':
            # Between 5 and 15 days
            five_days = today + timedelta(days=5)
            fifteen_days = today + timedelta(days=15)
            query = query.filter(
                Certificado.data_vencimento > five_days,
                Certificado.data_vencimento <= fifteen_days
            )
        elif status == 'critico':
            # Less than 5 days but not expired
            five_days = today + timedelta(days=5)
            query = query.filter(
                Certificado.data_vencimento > today,
                Certificado.data_vencimento <= five_days
            )
        elif status == 'vencido':
            # Expired
            query = query.filter(Certificado.data_vencimento <= today)
    
    if tipo:
        query = query.filter(Certificado.tipo == tipo)
    
    # Order by expiration date
    query = query.order_by(Certificado.data_vencimento)
    
    # Paginate
    certificados = query.paginate(page=page, per_page=per_page)
    
    # Get all companies for filter dropdown
    empresas = Empresa.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).all()
    
    return render_template(
        'certificados/index.html',
        certificados=certificados,
        empresas=empresas,
        tipo_choices=TIPO_CERTIFICADO_CHOICES,
        empresa_id=empresa_id,
        status=status,
        tipo=tipo
    )

@app.route('/certificados/upload', methods=['GET', 'POST'])
@login_required
def upload_certificado():
    form = CertificadoUploadForm()
    
    # Populate company choices
    empresas = Empresa.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).all()
    form.empresa_id.choices = [(e.id, e.razao_social) for e in empresas]
    
    if form.validate_on_submit():
        try:
            # Generate a unique filename
            filename = secure_filename(form.arquivo.data.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Upload file to S3
            s3_path = upload_certificate_to_s3(
                form.arquivo.data,
                unique_filename
            )
            
            # Encrypt password
            encrypted_password, iv = encrypt_certificate_password(form.senha.data)
            
            # Create certificate record
            certificado = Certificado(
                tipo=form.tipo.data,
                nome=form.nome.data,
                data_emissao=form.data_emissao.data,
                data_vencimento=form.data_vencimento.data,
                arquivo_path=s3_path,
                senha_encrypted=encrypted_password,
                iv=iv,
                empresa_id=form.empresa_id.data,
                uploader_id=current_user.id
            )
            
            db.session.add(certificado)
            db.session.commit()
            
            log_audit(
                current_user.id,
                'Certificado Cadastrado',
                f'Certificado {certificado.nome} cadastrado para a empresa ID {certificado.empresa_id}'
            )
            
            flash('Certificado enviado com sucesso!', 'success')
            return redirect(url_for('certificados'))
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload do certificado: {e}")
            flash(f'Erro ao fazer upload do certificado: {str(e)}', 'danger')
    
    return render_template('certificados/upload.html', form=form)

@app.route('/certificados/<int:id>')
@login_required
def view_certificado(id):
    certificado = Certificado.query.get_or_404(id)
    
    # Check if user has access to this certificate
    empresa = Empresa.query.get(certificado.empresa_id)
    if empresa.organizacao_id != current_user.organizacao_id:
        abort(403)
    
    # Log view
    log_audit(
        current_user.id,
        'Visualização de Certificado',
        f'Certificado {certificado.nome} visualizado'
    )
    
    return render_template('certificados/view.html', certificado=certificado)

# Company routes
@app.route('/empresas')
@login_required
def empresas():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    grupo = request.args.get('grupo')
    search = request.args.get('search')
    
    # Base query
    query = Empresa.query.filter_by(organizacao_id=current_user.organizacao_id)
    
    # Apply filters
    if grupo:
        query = query.filter_by(grupo=grupo)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Empresa.razao_social.ilike(search_term)) |
            (Empresa.nome_fantasia.ilike(search_term)) |
            (Empresa.cnpj.ilike(search_term))
        )
    
    # Paginate
    empresas = query.paginate(page=page, per_page=per_page)
    
    # Get all groups for filter
    grupos = db.session.query(Empresa.grupo).filter(
        Empresa.organizacao_id == current_user.organizacao_id,
        Empresa.grupo != None,
        Empresa.grupo != ''
    ).distinct().all()
    grupos = [g[0] for g in grupos]
    
    return render_template(
        'empresas/index.html',
        empresas=empresas,
        grupos=grupos,
        grupo_filtro=grupo,
        search=search
    )

@app.route('/empresas/create', methods=['GET', 'POST'])
@login_required
def create_empresa():
    form = EmpresaForm()
    
    if form.validate_on_submit():
        empresa = Empresa(
            razao_social=form.razao_social.data,
            nome_fantasia=form.nome_fantasia.data,
            cnpj=form.cnpj.data,
            grupo=form.grupo.data,
            email_contato=form.email_contato.data,
            telefone=form.telefone.data,
            organizacao_id=current_user.organizacao_id
        )
        
        db.session.add(empresa)
        db.session.commit()
        
        log_audit(
            current_user.id,
            'Empresa Cadastrada',
            f'Empresa {empresa.razao_social} cadastrada'
        )
        
        flash('Empresa cadastrada com sucesso!', 'success')
        return redirect(url_for('empresas'))
    
    return render_template('empresas/create.html', form=form)

@app.route('/empresas/<int:id>')
@login_required
def view_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    
    # Check if user has access to this company
    if empresa.organizacao_id != current_user.organizacao_id:
        abort(403)
    
    # Get certificates for this company
    certificados = Certificado.query.filter_by(empresa_id=id).all()
    
    # Log view
    log_audit(
        current_user.id,
        'Visualização de Empresa',
        f'Empresa {empresa.razao_social} visualizada'
    )
    
    return render_template(
        'empresas/view.html',
        empresa=empresa,
        certificados=certificados
    )

@app.route('/empresas/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    
    # Check if user has access to this company
    if empresa.organizacao_id != current_user.organizacao_id:
        abort(403)
    
    # Check if user is admin
    if not current_user.is_admin():
        flash('Você não tem permissão para editar empresas.', 'danger')
        return redirect(url_for('view_empresa', id=id))
    
    form = EmpresaForm(obj=empresa)
    
    if form.validate_on_submit():
        empresa.razao_social = form.razao_social.data
        empresa.nome_fantasia = form.nome_fantasia.data
        empresa.cnpj = form.cnpj.data
        empresa.grupo = form.grupo.data
        empresa.email_contato = form.email_contato.data
        empresa.telefone = form.telefone.data
        
        db.session.commit()
        
        log_audit(
            current_user.id,
            'Empresa Editada',
            f'Empresa {empresa.razao_social} editada'
        )
        
        flash('Empresa atualizada com sucesso!', 'success')
        return redirect(url_for('view_empresa', id=id))
    
    return render_template('empresas/edit.html', form=form, empresa=empresa)

# User management routes
@app.route('/usuarios')
@login_required
def usuarios():
    # Only admins can access this page
    if not current_user.is_admin():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    usuarios = Usuario.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).all()
    
    # Get pending invitations
    convites = ConviteUsuario.query.filter_by(
        organizacao_id=current_user.organizacao_id,
        usado=False
    ).filter(
        ConviteUsuario.data_expiracao > datetime.utcnow()
    ).all()
    
    return render_template(
        'usuarios/index.html',
        usuarios=usuarios,
        convites=convites
    )

@app.route('/usuarios/invite', methods=['GET', 'POST'])
@login_required
def invite_usuario():
    # Only admins can access this page
    if not current_user.is_admin():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ConviteForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = Usuario.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Já existe um usuário com este email.', 'danger')
            return render_template('usuarios/invite.html', form=form)
        
        # Create invitation
        convite = ConviteUsuario(
            email=form.email.data,
            tipo_usuario=form.tipo.data,
            organizacao_id=current_user.organizacao_id,
            criado_por=current_user.id
        )
        
        db.session.add(convite)
        db.session.commit()
        
        # TODO: Send email with invitation link
        
        log_audit(
            current_user.id,
            'Convite Enviado',
            f'Convite enviado para {convite.email}'
        )
        
        flash('Convite enviado com sucesso!', 'success')
        return redirect(url_for('usuarios'))
    
    return render_template('usuarios/invite.html', form=form)

@app.route('/usuarios/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_usuario_status(id):
    # Only admins can access this page
    if not current_user.is_admin():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Check if user has access to this user
    if usuario.organizacao_id != current_user.organizacao_id:
        abort(403)
    
    # Cannot deactivate yourself
    if usuario.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'danger')
        return redirect(url_for('usuarios'))
    
    # Toggle status
    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    status = 'ativado' if usuario.ativo else 'desativado'
    
    log_audit(
        current_user.id,
        f'Usuário {status.capitalize()}',
        f'Usuário {usuario.nome} {status}'
    )
    
    flash(f'Usuário {status} com sucesso!', 'success')
    return redirect(url_for('usuarios'))

# Alerts routes
@app.route('/alertas')
@login_required
def alertas():
    # Get all certificates expiring in the next 30 days
    today = datetime.utcnow().date()
    thirty_days = today + timedelta(days=30)
    
    certificados = Certificado.query.join(Empresa).filter(
        Empresa.organizacao_id == current_user.organizacao_id,
        Certificado.data_vencimento.between(today, thirty_days)
    ).order_by(Certificado.data_vencimento).all()
    
    # Group certificates by expiration status
    critical = []  # 0-5 days
    warning = []   # 6-15 days
    attention = [] # 16-30 days
    
    for cert in certificados:
        days = cert.dias_para_vencimento()
        if days <= 5:
            critical.append(cert)
        elif days <= 15:
            warning.append(cert)
        else:
            attention.append(cert)
    
    return render_template(
        'alertas/index.html',
        critical=critical,
        warning=warning,
        attention=attention
    )

# Audit log routes
@app.route('/auditoria')
@login_required
def auditoria():
    # Only admins can access this page
    if not current_user.is_admin():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    usuario_id = request.args.get('usuario_id', type=int)
    acao = request.args.get('acao')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Base query
    query = LogAuditoria.query.join(Usuario).filter(
        Usuario.organizacao_id == current_user.organizacao_id
    )
    
    # Apply filters
    if usuario_id:
        query = query.filter(LogAuditoria.usuario_id == usuario_id)
    
    if acao:
        query = query.filter(LogAuditoria.acao.ilike(f"%{acao}%"))
    
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(LogAuditoria.data_hora >= data_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Add one day to include the end date
            data_fim = data_fim + timedelta(days=1)
            query = query.filter(LogAuditoria.data_hora < data_fim)
        except ValueError:
            pass
    
    # Order by date descending
    query = query.order_by(LogAuditoria.data_hora.desc())
    
    # Paginate
    logs = query.paginate(page=page, per_page=per_page)
    
    # Get all users for filter dropdown
    usuarios = Usuario.query.filter_by(
        organizacao_id=current_user.organizacao_id
    ).all()
    
    return render_template(
        'auditoria/index.html',
        logs=logs,
        usuarios=usuarios,
        usuario_id=usuario_id,
        acao=acao,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

# Profile routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = PerfilForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check current password
        if form.current_password.data and not current_user.verify_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return render_template('profile/index.html', form=form)
        
        # Update profile
        current_user.nome = form.nome.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.password = form.new_password.data
            log_audit(current_user.id, 'Senha Alterada', 'Senha alterada pelo usuário')
        
        db.session.commit()
        
        log_audit(current_user.id, 'Perfil Atualizado', 'Perfil atualizado pelo usuário')
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile/index.html', form=form)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Scheduled task to check for expiring certificates
@app.before_request
def before_request():
    # Run once a day
    now = datetime.utcnow()
    last_check = app.config.get('LAST_CERTIFICATE_CHECK')
    
    if not last_check or (now - last_check).days >= 1:
        check_for_expiring_certificates()
        app.config['LAST_CERTIFICATE_CHECK'] = now
