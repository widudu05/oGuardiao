from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# Define user types
TIPO_USUARIO_MASTER_ADMIN = 'master_admin'
TIPO_USUARIO_ADMIN = 'admin'
TIPO_USUARIO_OPERADOR = 'operador'

TIPO_USUARIO_CHOICES = [
    (TIPO_USUARIO_MASTER_ADMIN, 'Master Admin'),
    (TIPO_USUARIO_ADMIN, 'Administrador'),
    (TIPO_USUARIO_OPERADOR, 'Operador')
]

# Define certificate types
TIPO_CERTIFICADO_ECNPJ = 'e-cnpj'
TIPO_CERTIFICADO_ECPF = 'e-cpf'

TIPO_CERTIFICADO_CHOICES = [
    (TIPO_CERTIFICADO_ECNPJ, 'e-CNPJ'),
    (TIPO_CERTIFICADO_ECPF, 'e-CPF')
]

# Define plans
PLANO_GRATUITO = 'gratuito'
PLANO_BASICO = 'basico'
PLANO_PROFISSIONAL = 'profissional'
PLANO_ENTERPRISE = 'enterprise'

PLANO_CHOICES = [
    (PLANO_GRATUITO, 'Gratuito'),
    (PLANO_BASICO, 'Básico'),
    (PLANO_PROFISSIONAL, 'Profissional'),
    (PLANO_ENTERPRISE, 'Enterprise')
]


class Organizacao(db.Model):
    """Organization model - represents a client with a specific plan"""
    __tablename__ = 'organizacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    email_contato = db.Column(db.String(100), nullable=False)
    plano = db.Column(db.String(20), nullable=False, default=PLANO_GRATUITO)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relationships
    usuarios = db.relationship('Usuario', backref='organizacao', lazy=True)
    empresas = db.relationship('Empresa', backref='organizacao', lazy=True)
    
    def __repr__(self):
        return f'<Organizacao {self.nome}>'


class Usuario(UserMixin, db.Model):
    """User model with role-based permissions"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default=TIPO_USUARIO_OPERADOR)
    organizacao_id = db.Column(db.Integer, db.ForeignKey('organizacoes.id'))
    ativo = db.Column(db.Boolean, default=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    
    # Relationships
    logs = db.relationship('LogAuditoria', backref='usuario', lazy=True)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_master_admin(self):
        return self.tipo == TIPO_USUARIO_MASTER_ADMIN
    
    def is_admin(self):
        return self.tipo in [TIPO_USUARIO_MASTER_ADMIN, TIPO_USUARIO_ADMIN]
    
    def __repr__(self):
        return f'<Usuario {self.nome}>'


class Empresa(db.Model):
    """Company model - can have multiple certificates"""
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(100), nullable=False)
    nome_fantasia = db.Column(db.String(100))
    cnpj = db.Column(db.String(18), nullable=False)
    grupo = db.Column(db.String(50))
    email_contato = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    organizacao_id = db.Column(db.Integer, db.ForeignKey('organizacoes.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    certificados = db.relationship('Certificado', backref='empresa', lazy=True)
    
    def __repr__(self):
        return f'<Empresa {self.razao_social}>'


class Certificado(db.Model):
    """Digital certificate model with encryption"""
    __tablename__ = 'certificados'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_emissao = db.Column(db.DateTime, nullable=False)
    data_vencimento = db.Column(db.DateTime, nullable=False)
    arquivo_path = db.Column(db.String(255), nullable=False)  # S3 path
    senha_encrypted = db.Column(db.String(255), nullable=False)  # AES-256 encrypted
    iv = db.Column(db.String(64), nullable=False)  # Initialization vector for AES
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('Usuario')
    
    def __repr__(self):
        return f'<Certificado {self.nome}>'
    
    def dias_para_vencimento(self):
        """Calculate days until certificate expiration"""
        hoje = datetime.utcnow().date()
        vencimento = self.data_vencimento.date()
        return (vencimento - hoje).days
    
    def status(self):
        """Return certificate status based on expiration date"""
        dias = self.dias_para_vencimento()
        
        if dias < 0:
            return "Vencido"
        elif dias <= 5:
            return "Crítico"
        elif dias <= 15:
            return "Alerta"
        elif dias <= 30:
            return "Atenção"
        else:
            return "Válido"


class LogAuditoria(db.Model):
    """Audit log for tracking user actions"""
    __tablename__ = 'logs_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    endereco_ip = db.Column(db.String(45))  # IPv6-compatible length
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LogAuditoria {self.acao}>'


class ConviteUsuario(db.Model):
    """User invitation model"""
    __tablename__ = 'convites_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    tipo_usuario = db.Column(db.String(20), nullable=False, default=TIPO_USUARIO_OPERADOR)
    organizacao_id = db.Column(db.Integer, db.ForeignKey('organizacoes.id'), nullable=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_expiracao = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    usado = db.Column(db.Boolean, default=False)
    
    # Relationships
    organizacao = db.relationship('Organizacao')
    criador = db.relationship('Usuario')
    
    def expirado(self):
        """Check if invitation has expired"""
        return datetime.utcnow() > self.data_expiracao
    
    def __repr__(self):
        return f'<ConviteUsuario {self.email}>'


class Alerta(db.Model):
    """Alert model for certificate expiration notifications"""
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    certificado_id = db.Column(db.Integer, db.ForeignKey('certificados.id'), nullable=False)
    dias_restantes = db.Column(db.Integer, nullable=False)
    notificado = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    certificado = db.relationship('Certificado')
    
    def __repr__(self):
        return f'<Alerta {self.certificado_id} - {self.dias_restantes} dias>'
