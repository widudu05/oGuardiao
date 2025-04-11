from flask import render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta
from functools import wraps
from app import app, db, login_manager
from models import User, Organization, UserInvite, AuditLog
from forms import LoginForm, RegistrationForm, AcceptInviteForm, MFASetupForm, ProfileForm
from utils import generate_mfa_secret, generate_mfa_qr_code, verify_mfa_code, log_audit_event

# Role decorator functions
def master_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'master_admin':
            flash('Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['master_admin', 'admin']:
            flash('Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválidos', 'error')
            return render_template('login.html', form=form)
        
        # Check for MFA if enabled
        if user.mfa_enabled:
            # Store partial login state
            g.partial_login_user_id = user.id
            return redirect(url_for('mfa_verify'))
        
        # Log successful login
        log_audit_event(
            user.id, 
            'login', 
            f"Login bem-sucedido",
            request.remote_addr
        )
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirect to the page user was trying to access
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/mfa-verify', methods=['GET', 'POST'])
def mfa_verify():
    # Check if we have a partial login user
    user_id = getattr(g, 'partial_login_user_id', None)
    
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user or not user.mfa_secret:
        flash('Erro na autenticação MFA', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        
        if verify_mfa_code(user.mfa_secret, code):
            # MFA successful, complete login
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_audit_event(
                user.id,
                'login_mfa',
                f"Login com MFA bem-sucedido",
                request.remote_addr
            )
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('Código MFA inválido', 'error')
    
    return render_template('mfa_verify.html')

@app.route('/logout')
@login_required
def logout():
    log_audit_event(
        current_user.id,
        'logout',
        f"Logout bem-sucedido",
        request.remote_addr
    )
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create organization
        organization = Organization(
            name=form.organization_name.data,
            cnpj=form.cnpj.data,
            responsible=form.name.data,
            plan='basic'  # Default plan
        )
        db.session.add(organization)
        db.session.flush()  # Get ID without committing
        
        # Create master admin user
        user = User(
            name=form.name.data,
            email=form.email.data,
            role='master_admin',
            organization_id=organization.id
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('Cadastro realizado com sucesso! Por favor, faça login.', 'success')
            
            log_audit_event(
                user.id,
                'register',
                f"Nova organização: {organization.name}",
                request.remote_addr
            )
            
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('Ocorreu um erro durante o cadastro. Por favor, tente novamente.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/accept-invite/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    # Find the invitation
    invite = UserInvite.query.filter_by(token=token).first()
    
    if not invite or invite.expires_at < datetime.utcnow() or invite.accepted:
        flash('Convite inválido ou expirado', 'error')
        return redirect(url_for('index'))
    
    form = AcceptInviteForm()
    form.token.data = token
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            name=form.name.data,
            email=invite.email,
            role=invite.role,
            organization_id=invite.organization_id
        )
        user.set_password(form.password.data)
        
        # Mark invite as accepted
        invite.accepted = True
        
        db.session.add(user)
        
        try:
            db.session.commit()
            
            log_audit_event(
                invite.invited_by,
                'invite_accepted',
                f"Convite aceito por {user.email} com função {user.role}",
                request.remote_addr
            )
            
            flash('Conta criada com sucesso! Por favor, faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Invite acceptance error: {str(e)}")
            flash('Ocorreu um erro ao criar sua conta. Por favor, tente novamente.', 'error')
    
    return render_template('accept_invite.html', form=form, invite=invite)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        if form.current_password.data:
            # Check current password before allowing changes
            if not current_user.check_password(form.current_password.data):
                flash('Senha atual incorreta', 'error')
                return render_template('profile.html', form=form)
            
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
                flash('Senha atualizada com sucesso', 'success')
                
                log_audit_event(
                    current_user.id,
                    'password_change',
                    f"Senha alterada",
                    request.remote_addr
                )
        
        # Update name
        if current_user.name != form.name.data:
            current_user.name = form.name.data
            flash('Perfil atualizado com sucesso', 'success')
        
        db.session.commit()
        
    elif request.method == 'GET':
        form.name.data = current_user.name
    
    # Get MFA status for display
    mfa_enabled = current_user.mfa_enabled
    
    return render_template('profile.html', form=form, mfa_enabled=mfa_enabled)

@app.route('/mfa-setup', methods=['GET', 'POST'])
@login_required
def mfa_setup():
    form = MFASetupForm()
    
    # Generate secret if not already set up
    if not current_user.mfa_secret:
        current_user.mfa_secret = generate_mfa_secret()
        db.session.commit()
    
    # Generate QR code
    qr_code = generate_mfa_qr_code(current_user.email, current_user.mfa_secret)
    
    if form.validate_on_submit():
        # Verify submitted code
        if verify_mfa_code(current_user.mfa_secret, form.code.data):
            current_user.mfa_enabled = True
            db.session.commit()
            
            log_audit_event(
                current_user.id,
                'mfa_enabled',
                f"Autenticação em dois fatores ativada",
                request.remote_addr
            )
            
            flash('Autenticação em dois fatores ativada com sucesso!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Código inválido, tente novamente', 'error')
    
    return render_template('mfa_setup.html', form=form, qr_code=qr_code, secret=current_user.mfa_secret)

@app.route('/mfa-disable', methods=['POST'])
@login_required
def mfa_disable():
    password = request.form.get('password')
    
    if not password or not current_user.check_password(password):
        flash('Senha incorreta', 'error')
        return redirect(url_for('profile'))
    
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.session.commit()
    
    log_audit_event(
        current_user.id,
        'mfa_disabled',
        f"Autenticação em dois fatores desativada",
        request.remote_addr
    )
    
    flash('Autenticação em dois fatores desativada com sucesso', 'success')
    return redirect(url_for('profile'))

@app.route('/dashboard')
@login_required
def dashboard():
    from models import Certificate, Company
    from datetime import datetime, timedelta
    
    # Get certificates expiring in the next 30 days
    today = datetime.now().date()
    expiry_date_limit = today + timedelta(days=30)
    
    # Get organization ID (all users belong to an organization)
    org_id = current_user.organization_id
    
    # Query certificates based on user role
    if current_user.role in ['master_admin', 'admin']:
        # Admins can see all certificates in their organization
        expiring_certificates = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= expiry_date_limit,
                Certificate.expiry_date >= today
            )
            .order_by(Certificate.expiry_date)
            .limit(10)
            .all()
        )
        
        # Get some statistics
        total_companies = Company.query.filter_by(organization_id=org_id).count()
        total_certificates = (
            Certificate.query
            .join(Company)
            .filter(Company.organization_id == org_id)
            .count()
        )
        
        # Get certificates by type for chart
        ecnpj_count = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.type == 'e-cnpj'
            )
            .count()
        )
        
        ecpf_count = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.type == 'e-cpf'
            )
            .count()
        )
        
        # Get expiring certificates count for different periods
        expiring_30d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=30),
                Certificate.expiry_date > today
            )
            .count()
        )
        
        expiring_60d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=60),
                Certificate.expiry_date > today + timedelta(days=30)
            )
            .count()
        )
        
        expiring_90d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=90),
                Certificate.expiry_date > today + timedelta(days=60)
            )
            .count()
        )
        
        # Get recent activity from audit log
        from models import AuditLog
        recent_activity = (
            AuditLog.query
            .join(User)
            .filter(User.organization_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(10)
            .all()
        )
    else:
        # Operators see a limited dashboard
        expiring_certificates = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= expiry_date_limit,
                Certificate.expiry_date >= today
            )
            .order_by(Certificate.expiry_date)
            .limit(10)
            .all()
        )
        
        total_companies = Company.query.filter_by(organization_id=org_id).count()
        total_certificates = (
            Certificate.query
            .join(Company)
            .filter(Company.organization_id == org_id)
            .count()
        )
        
        ecnpj_count = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.type == 'e-cnpj'
            )
            .count()
        )
        
        ecpf_count = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.type == 'e-cpf'
            )
            .count()
        )
        
        expiring_30d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=30),
                Certificate.expiry_date > today
            )
            .count()
        )
        
        expiring_60d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=60),
                Certificate.expiry_date > today + timedelta(days=30)
            )
            .count()
        )
        
        expiring_90d = (
            Certificate.query
            .join(Company)
            .filter(
                Company.organization_id == org_id,
                Certificate.expiry_date <= today + timedelta(days=90),
                Certificate.expiry_date > today + timedelta(days=60)
            )
            .count()
        )
        
        recent_activity = []  # Operators don't see audit logs
    
    return render_template(
        'dashboard.html',
        expiring_certificates=expiring_certificates,
        total_companies=total_companies,
        total_certificates=total_certificates,
        ecnpj_count=ecnpj_count,
        ecpf_count=ecpf_count,
        expiring_30d=expiring_30d,
        expiring_60d=expiring_60d,
        expiring_90d=expiring_90d,
        recent_activity=recent_activity
    )

# Company routes
@app.route('/companies')
@login_required
def companies():
    from models import Company, Group
    
    # Get organization ID (all users belong to an organization)
    org_id = current_user.organization_id
    
    # Get groups for filtering
    groups = Group.query.filter_by(organization_id=org_id).all()
    selected_group_id = request.args.get('group_id', type=int)
    
    # Base query
    query = Company.query.filter_by(organization_id=org_id)
    
    # Apply filter if group_id is provided
    if selected_group_id:
        query = query.filter_by(group_id=selected_group_id)
    
    # Search filter
    search = request.args.get('search', '')
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%') | Company.cnpj.ilike(f'%{search}%'))
    
    # Get companies
    companies = query.order_by(Company.name).all()
    
    return render_template(
        'companies/index.html',
        companies=companies,
        groups=groups,
        selected_group_id=selected_group_id,
        search=search
    )

@app.route('/companies/create', methods=['GET', 'POST'])
@login_required
def create_company():
    from forms import CompanyForm
    
    form = CompanyForm(organization_id=current_user.organization_id)
    
    if form.validate_on_submit():
        from models import Company
        
        company = Company(
            name=form.name.data,
            trade_name=form.trade_name.data,
            cnpj=form.cnpj.data,
            organization_id=current_user.organization_id,
            group_id=form.group_id.data if form.group_id.data and form.group_id.data > 0 else None
        )
        
        db.session.add(company)
        
        try:
            db.session.commit()
            
            log_audit_event(
                current_user.id,
                'company_created',
                f"Empresa criada: {company.name} ({company.cnpj})",
                request.remote_addr
            )
            
            flash('Empresa criada com sucesso!', 'success')
            return redirect(url_for('companies'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Company creation error: {str(e)}")
            flash('Ocorreu um erro ao criar a empresa. Por favor, tente novamente.', 'error')
    
    return render_template('companies/create.html', form=form)

@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    from models import Company
    from forms import CompanyForm
    
    company = Company.query.filter_by(
        id=company_id, 
        organization_id=current_user.organization_id
    ).first_or_404()
    
    form = CompanyForm(organization_id=current_user.organization_id, obj=company)
    
    if form.validate_on_submit():
        company.name = form.name.data
        company.trade_name = form.trade_name.data
        company.cnpj = form.cnpj.data
        company.group_id = form.group_id.data if form.group_id.data and form.group_id.data > 0 else None
        
        try:
            db.session.commit()
            
            log_audit_event(
                current_user.id,
                'company_updated',
                f"Empresa atualizada: {company.name} ({company.cnpj})",
                request.remote_addr
            )
            
            flash('Empresa atualizada com sucesso!', 'success')
            return redirect(url_for('companies'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Company update error: {str(e)}")
            flash('Ocorreu um erro ao atualizar a empresa. Por favor, tente novamente.', 'error')
    
    return render_template('companies/edit.html', form=form, company=company)

@app.route('/companies/<int:company_id>/delete', methods=['POST'])
@login_required
def delete_company(company_id):
    from models import Company, Certificate
    
    company = Company.query.filter_by(
        id=company_id, 
        organization_id=current_user.organization_id
    ).first_or_404()
    
    # Check if there are certificates associated with this company
    certificates = Certificate.query.filter_by(company_id=company.id).count()
    
    if certificates > 0:
        flash(f'Não é possível excluir esta empresa porque existem {certificates} certificados vinculados a ela.', 'error')
        return redirect(url_for('companies'))
    
    try:
        company_name = company.name
        db.session.delete(company)
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'company_deleted',
            f"Empresa excluída: {company_name}",
            request.remote_addr
        )
        
        flash('Empresa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Company deletion error: {str(e)}")
        flash('Ocorreu um erro ao excluir a empresa.', 'error')
    
    return redirect(url_for('companies'))

# Groups routes
@app.route('/groups')
@login_required
def groups():
    from models import Group
    
    groups = Group.query.filter_by(organization_id=current_user.organization_id).order_by(Group.name).all()
    
    return render_template('groups/index.html', groups=groups)

@app.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    from forms import GroupForm
    from models import Group
    
    form = GroupForm()
    
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            description=form.description.data,
            organization_id=current_user.organization_id
        )
        
        db.session.add(group)
        
        try:
            db.session.commit()
            
            log_audit_event(
                current_user.id,
                'group_created',
                f"Grupo criado: {group.name}",
                request.remote_addr
            )
            
            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('groups'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Group creation error: {str(e)}")
            flash('Ocorreu um erro ao criar o grupo. Por favor, tente novamente.', 'error')
    
    return render_template('groups/create.html', form=form)

@app.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    from models import Group
    from forms import GroupForm
    
    group = Group.query.filter_by(
        id=group_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    form = GroupForm(obj=group)
    
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        
        try:
            db.session.commit()
            
            log_audit_event(
                current_user.id,
                'group_updated',
                f"Grupo atualizado: {group.name}",
                request.remote_addr
            )
            
            flash('Grupo atualizado com sucesso!', 'success')
            return redirect(url_for('groups'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Group update error: {str(e)}")
            flash('Ocorreu um erro ao atualizar o grupo. Por favor, tente novamente.', 'error')
    
    return render_template('groups/edit.html', form=form, group=group)

@app.route('/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    from models import Group, Company
    
    group = Group.query.filter_by(
        id=group_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    # Check if there are companies in this group
    companies = Company.query.filter_by(group_id=group.id).count()
    
    if companies > 0:
        flash(f'Não é possível excluir este grupo porque existem {companies} empresas vinculadas a ele.', 'error')
        return redirect(url_for('groups'))
    
    try:
        group_name = group.name
        db.session.delete(group)
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'group_deleted',
            f"Grupo excluído: {group_name}",
            request.remote_addr
        )
        
        flash('Grupo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Group deletion error: {str(e)}")
        flash('Ocorreu um erro ao excluir o grupo.', 'error')
    
    return redirect(url_for('groups'))

# Certificates routes
@app.route('/certificates')
@login_required
def certificates():
    from models import Certificate, Company
    
    # Base query
    query = (
        Certificate.query
        .join(Company)
        .filter(Company.organization_id == current_user.organization_id)
    )
    
    # Apply filters
    company_id = request.args.get('company_id', type=int)
    if company_id:
        query = query.filter(Certificate.company_id == company_id)
    
    type_filter = request.args.get('type')
    if type_filter in ['e-cnpj', 'e-cpf']:
        query = query.filter(Certificate.type == type_filter)
    
    status = request.args.get('status')
    today = datetime.now().date()
    if status == 'valid':
        query = query.filter(Certificate.expiry_date > today)
    elif status == 'expired':
        query = query.filter(Certificate.expiry_date <= today)
    elif status == 'expiring-soon':
        query = query.filter(
            Certificate.expiry_date <= today + timedelta(days=30),
            Certificate.expiry_date > today
        )
    
    # Search filter
    search = request.args.get('search', '')
    if search:
        query = query.filter(Certificate.name.ilike(f'%{search}%'))
    
    # Get certificates
    certificates = query.order_by(Certificate.expiry_date).all()
    
    # Get companies for filter dropdown
    companies = Company.query.filter_by(organization_id=current_user.organization_id).order_by(Company.name).all()
    
    return render_template(
        'certificates/index.html',
        certificates=certificates,
        companies=companies,
        company_id=company_id,
        type_filter=type_filter,
        status=status,
        search=search,
        today=today
    )

@app.route('/certificates/upload', methods=['GET', 'POST'])
@login_required
def upload_certificate():
    from forms import CertificateUploadForm
    
    form = CertificateUploadForm(organization_id=current_user.organization_id)
    
    if form.validate_on_submit():
        from models import Certificate
        from utils import encrypt_certificate_password
        import os
        
        # Get the certificate file
        cert_file = form.certificate_file.data
        
        # Generate a secure filename
        import uuid
        filename = f"{uuid.uuid4()}.{cert_file.filename.split('.')[-1]}"
        
        # Create certificates directory if it doesn't exist
        os.makedirs('certificates', exist_ok=True)
        
        # Save the file temporarily
        file_path = os.path.join('certificates', filename)
        cert_file.save(file_path)
        
        # Encrypt the certificate password
        encrypted_password, iv = encrypt_certificate_password(form.password.data)
        
        # Create certificate record
        certificate = Certificate(
            name=form.name.data,
            type=form.type.data,
            file_name=filename,
            encrypted_password=encrypted_password,
            iv=iv,
            company_id=form.company_id.data,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            created_by=current_user.id
        )
        
        db.session.add(certificate)
        
        try:
            db.session.commit()
            
            # In production, this would upload to AWS S3 and delete the local file
            # certificate.s3_key = 'path/to/s3/file'
            
            log_audit_event(
                current_user.id,
                'certificate_uploaded',
                f"Certificado enviado: {certificate.name} - {certificate.type}",
                request.remote_addr
            )
            
            flash('Certificado enviado com sucesso!', 'success')
            return redirect(url_for('certificates'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Certificate upload error: {str(e)}")
            flash('Ocorreu um erro ao enviar o certificado. Por favor, tente novamente.', 'error')
            
            # Remove the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return render_template('certificates/upload.html', form=form)

@app.route('/certificates/<int:certificate_id>/view')
@login_required
def view_certificate(certificate_id):
    from models import Certificate, Company
    
    # Get the certificate, ensuring it belongs to the user's organization
    certificate = (
        Certificate.query
        .join(Company)
        .filter(
            Certificate.id == certificate_id,
            Company.organization_id == current_user.organization_id
        )
        .first_or_404()
    )
    
    # Log the view
    log_audit_event(
        current_user.id,
        'certificate_viewed',
        f"Certificado visualizado: {certificate.name}",
        request.remote_addr
    )
    
    return render_template('certificates/view.html', certificate=certificate)

@app.route('/certificates/<int:certificate_id>/delete', methods=['POST'])
@login_required
def delete_certificate(certificate_id):
    from models import Certificate, Company
    
    # Get the certificate, ensuring it belongs to the user's organization
    certificate = (
        Certificate.query
        .join(Company)
        .filter(
            Certificate.id == certificate_id,
            Company.organization_id == current_user.organization_id
        )
        .first_or_404()
    )
    
    try:
        cert_name = certificate.name
        
        # Delete the certificate file
        # In production, this would delete from S3
        import os
        file_path = os.path.join('certificates', certificate.file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(certificate)
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'certificate_deleted',
            f"Certificado excluído: {cert_name}",
            request.remote_addr
        )
        
        flash('Certificado excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Certificate deletion error: {str(e)}")
        flash('Ocorreu um erro ao excluir o certificado.', 'error')
    
    return redirect(url_for('certificates'))

# Users and invitations routes
@app.route('/users')
@login_required
@admin_required
def users():
    from models import User
    
    # Get users for this organization
    users = User.query.filter_by(organization_id=current_user.organization_id).order_by(User.name).all()
    
    return render_template('users/index.html', users=users)

@app.route('/users/invite', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    from forms import UserInviteForm
    
    form = UserInviteForm()
    
    if form.validate_on_submit():
        from models import UserInvite
        from utils import send_invitation_email
        from datetime import datetime, timedelta
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            if existing_user.organization_id == current_user.organization_id:
                flash('Este usuário já pertence à sua organização.', 'error')
            else:
                flash('Este email já está registrado em outra organização.', 'error')
            return render_template('users/invite.html', form=form)
        
        # Check if there's an existing invite for this email
        existing_invite = UserInvite.query.filter_by(
            email=form.email.data,
            organization_id=current_user.organization_id,
            accepted=False
        ).first()
        
        if existing_invite:
            # Update the existing invite
            existing_invite.role = form.role.data
            existing_invite.invited_by = current_user.id
            existing_invite.expires_at = datetime.utcnow() + timedelta(days=7)
            existing_invite.token = UserInvite.generate_token()
            
            try:
                db.session.commit()
                
                # Send the invitation email
                if send_invitation_email(existing_invite):
                    flash('Convite reenviado com sucesso!', 'success')
                else:
                    flash('Convite criado, mas houve um erro ao enviar o email.', 'warning')
                
                log_audit_event(
                    current_user.id,
                    'user_invited',
                    f"Convite reenviado para {existing_invite.email} com função {existing_invite.role}",
                    request.remote_addr
                )
                
                return redirect(url_for('users'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Invite update error: {str(e)}")
                flash('Ocorreu um erro ao reenviar o convite. Por favor, tente novamente.', 'error')
        else:
            # Create a new invite
            invite = UserInvite(
                email=form.email.data,
                token=UserInvite.generate_token(),
                organization_id=current_user.organization_id,
                role=form.role.data,
                invited_by=current_user.id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(invite)
            
            try:
                db.session.commit()
                
                # Send the invitation email
                if send_invitation_email(invite):
                    flash('Convite enviado com sucesso!', 'success')
                else:
                    flash('Convite criado, mas houve um erro ao enviar o email.', 'warning')
                
                log_audit_event(
                    current_user.id,
                    'user_invited',
                    f"Convite enviado para {invite.email} com função {invite.role}",
                    request.remote_addr
                )
                
                return redirect(url_for('users'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Invite creation error: {str(e)}")
                flash('Ocorreu um erro ao enviar o convite. Por favor, tente novamente.', 'error')
    
    return render_template('users/invite.html', form=form)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Prevent deleting yourself
    if user_id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'error')
        return redirect(url_for('users'))
    
    # Only master admin can delete admin users
    user = User.query.filter_by(
        id=user_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if user.role == 'admin' and current_user.role != 'master_admin':
        flash('Apenas o administrador principal pode excluir outros administradores.', 'error')
        return redirect(url_for('users'))
    
    try:
        user_email = user.email
        db.session.delete(user)
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'user_deleted',
            f"Usuário excluído: {user_email}",
            request.remote_addr
        )
        
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"User deletion error: {str(e)}")
        flash('Ocorreu um erro ao excluir o usuário.', 'error')
    
    return redirect(url_for('users'))

# Audit logs
@app.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    from models import AuditLog, User
    
    # Apply filters
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action')
    
    # Base query - only show logs for users in same organization
    query = (
        AuditLog.query
        .join(User)
        .filter(User.organization_id == current_user.organization_id)
    )
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    # Date range filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
            query = query.filter(AuditLog.created_at < end)
        except ValueError:
            pass
    
    # Get logs
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=request.args.get('page', 1, type=int), per_page=50)
    
    # Get users for filter dropdown
    users = User.query.filter_by(organization_id=current_user.organization_id).order_by(User.name).all()
    
    # Get unique actions for filter dropdown
    actions = db.session.query(AuditLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template(
        'audit/index.html',
        logs=logs,
        users=users,
        actions=actions,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date
    )

# Reports
@app.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('reports.html')

@app.route('/reports/export-certificates')
@login_required
@admin_required
def export_certificates():
    from models import Certificate, Company
    import csv
    from io import StringIO
    
    # Get certificates for this organization
    certificates = (
        Certificate.query
        .join(Company)
        .filter(Company.organization_id == current_user.organization_id)
        .order_by(Certificate.expiry_date)
        .all()
    )
    
    # Create CSV file
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Nome', 'Tipo', 'Empresa', 'CNPJ', 'Data de Emissão', 
        'Data de Validade', 'Dias Restantes', 'Status'
    ])
    
    # Write data
    today = datetime.now().date()
    for cert in certificates:
        days_left = (cert.expiry_date - today).days
        if days_left < 0:
            status = 'Expirado'
        elif days_left <= 30:
            status = 'Expirando em breve'
        else:
            status = 'Válido'
        
        writer.writerow([
            cert.name,
            cert.type,
            cert.company.name,
            cert.company.cnpj,
            cert.issue_date.strftime('%d/%m/%Y'),
            cert.expiry_date.strftime('%d/%m/%Y'),
            days_left if days_left >= 0 else 0,
            status
        ])
    
    # Create response
    output.seek(0)
    
    log_audit_event(
        current_user.id,
        'report_generated',
        f"Relatório de certificados exportado",
        request.remote_addr
    )
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=certificados.csv'}
    )
