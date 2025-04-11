from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import Usuario, Organizacao, TIPO_USUARIO_CHOICES, TIPO_CERTIFICADO_CHOICES, PLANO_CHOICES
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    
class MFAForm(FlaskForm):
    code = StringField('Código MFA', validators=[DataRequired(), Length(6, 6)])

class RegistrationForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(1, 100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(8, 64, message='A senha deve ter pelo menos 8 caracteres')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas não coincidem')
    ])
    nome_organizacao = StringField('Nome da Organização', validators=[DataRequired()])
    cnpj = StringField('CNPJ', validators=[DataRequired(), Length(14, 18)])
    
    def validate_email(self, field):
        user = Usuario.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email já registrado. Por favor, use outro email.')
    
    def validate_cnpj(self, field):
        org = Organizacao.query.filter_by(cnpj=field.data).first()
        if org:
            raise ValidationError('CNPJ já registrado. Por favor, use outro CNPJ.')

class ConviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    tipo = SelectField('Tipo de Usuário', choices=TIPO_USUARIO_CHOICES, validators=[DataRequired()])

class RegisterFromInviteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(1, 100)])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(8, 64, message='A senha deve ter pelo menos 8 caracteres')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas não coincidem')
    ])
    token = HiddenField('Token', validators=[DataRequired()])

class OrganizacaoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(1, 100)])
    cnpj = StringField('CNPJ', validators=[DataRequired(), Length(14, 18)])
    email_contato = StringField('Email de Contato', validators=[DataRequired(), Email()])
    plano = SelectField('Plano', choices=PLANO_CHOICES, validators=[DataRequired()])

class EmpresaForm(FlaskForm):
    razao_social = StringField('Razão Social', validators=[DataRequired(), Length(1, 100)])
    nome_fantasia = StringField('Nome Fantasia', validators=[Length(0, 100)])
    cnpj = StringField('CNPJ', validators=[DataRequired(), Length(14, 18)])
    grupo = StringField('Grupo', validators=[Length(0, 50)])
    email_contato = StringField('Email de Contato', validators=[Email()])
    telefone = StringField('Telefone', validators=[Length(0, 20)])

class CertificadoUploadForm(FlaskForm):
    tipo = SelectField('Tipo de Certificado', choices=TIPO_CERTIFICADO_CHOICES, validators=[DataRequired()])
    nome = StringField('Nome do Certificado', validators=[DataRequired(), Length(1, 100)])
    arquivo = FileField('Arquivo do Certificado', validators=[
        FileRequired(),
        FileAllowed(['pfx', 'p12', 'cer'], 'Apenas arquivos PFX, P12 ou CER são permitidos.')
    ])
    senha = PasswordField('Senha do Certificado', validators=[DataRequired()])
    data_emissao = DateField('Data de Emissão', validators=[DataRequired()], format='%Y-%m-%d')
    data_vencimento = DateField('Data de Vencimento', validators=[DataRequired()], format='%Y-%m-%d')
    empresa_id = SelectField('Empresa', coerce=int, validators=[DataRequired()])
    
    def validate_data_vencimento(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('A data de vencimento não pode ser no passado.')
        
        if self.data_emissao.data and field.data <= self.data_emissao.data:
            raise ValidationError('A data de vencimento deve ser posterior à data de emissão.')

class PerfilForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(1, 100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Senha Atual')
    new_password = PasswordField('Nova Senha', validators=[Length(0, 64)])
    new_password2 = PasswordField('Confirmar Nova Senha', validators=[EqualTo('new_password')])
    
class SetupMFAForm(FlaskForm):
    code = StringField('Código de Verificação', validators=[DataRequired(), Length(6, 6)])
    secret = HiddenField('Secret', validators=[DataRequired()])
