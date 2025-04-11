from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
from models import User, Organization, Company
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    
class RegistrationForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[
        DataRequired(), 
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar senha', validators=[
        DataRequired(), 
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    organization_name = StringField('Nome da organização', validators=[DataRequired(), Length(min=3, max=100)])
    cnpj = StringField('CNPJ', validators=[
        DataRequired(),
        Regexp(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', message='CNPJ inválido. Use o formato: XX.XXX.XXX/XXXX-XX')
    ])
    terms = BooleanField('Eu aceito os termos de uso', validators=[DataRequired()])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está sendo usado. Por favor, use outro.')

class OrganizationForm(FlaskForm):
    name = StringField('Nome da organização', validators=[DataRequired(), Length(min=3, max=100)])
    cnpj = StringField('CNPJ', validators=[
        DataRequired(),
        Regexp(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', message='CNPJ inválido. Use o formato: XX.XXX.XXX/XXXX-XX')
    ])
    responsible = StringField('Responsável', validators=[DataRequired(), Length(min=3, max=100)])
    plan = SelectField('Plano', choices=[
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ], validators=[DataRequired()])

class GroupForm(FlaskForm):
    name = StringField('Nome do grupo', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])

class CompanyForm(FlaskForm):
    name = StringField('Razão Social', validators=[DataRequired(), Length(min=3, max=100)])
    trade_name = StringField('Nome Fantasia', validators=[Optional(), Length(max=100)])
    cnpj = StringField('CNPJ', validators=[
        DataRequired(),
        Regexp(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', message='CNPJ inválido. Use o formato: XX.XXX.XXX/XXXX-XX')
    ])
    group_id = SelectField('Grupo', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, organization_id=None, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        if organization_id:
            from models import Group
            from app import db
            
            self.group_id.choices = [(0, 'Sem grupo')] + [
                (g.id, g.name) 
                for g in Group.query.filter_by(organization_id=organization_id).all()
            ]

class CertificateUploadForm(FlaskForm):
    name = StringField('Nome do certificado', validators=[DataRequired(), Length(min=3, max=100)])
    type = SelectField('Tipo', choices=[
        ('e-cnpj', 'e-CNPJ'),
        ('e-cpf', 'e-CPF')
    ], validators=[DataRequired()])
    company_id = SelectField('Empresa', coerce=int, validators=[DataRequired()])
    certificate_file = FileField('Arquivo do certificado', validators=[
        FileRequired(),
        FileAllowed(['pfx', 'p12'], 'Apenas arquivos .pfx ou .p12 são permitidos.')
    ])
    password = PasswordField('Senha do certificado', validators=[DataRequired()])
    issue_date = DateField('Data de emissão', validators=[DataRequired()], format='%Y-%m-%d')
    expiry_date = DateField('Data de validade', validators=[DataRequired()], format='%Y-%m-%d')
    
    def __init__(self, *args, organization_id=None, **kwargs):
        super(CertificateUploadForm, self).__init__(*args, **kwargs)
        if organization_id:
            from models import Company
            
            self.company_id.choices = [
                (c.id, f"{c.name} ({c.cnpj})") 
                for c in Company.query.filter_by(organization_id=organization_id).all()
            ]
    
    def validate_expiry_date(self, expiry_date):
        if expiry_date.data < datetime.now().date():
            raise ValidationError('A data de validade não pode ser no passado.')
        
        if self.issue_date.data and expiry_date.data <= self.issue_date.data:
            raise ValidationError('A data de validade deve ser posterior à data de emissão.')

class UserInviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Função', choices=[
        ('admin', 'Administrador'),
        ('operator', 'Operador')
    ], validators=[DataRequired()])

class AcceptInviteForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=3, max=100)])
    password = PasswordField('Senha', validators=[
        DataRequired(), 
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar senha', validators=[
        DataRequired(), 
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    token = HiddenField('Token')

class ProfileForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=3, max=100)])
    current_password = PasswordField('Senha atual', validators=[Optional()])
    new_password = PasswordField('Nova senha', validators=[
        Optional(), 
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar nova senha', validators=[
        Optional(),
        EqualTo('new_password', message='As senhas devem ser iguais')
    ])
    
    def validate_confirm_password(self, confirm_password):
        if self.new_password.data and not confirm_password.data:
            raise ValidationError('Este campo é obrigatório quando você define uma nova senha.')

class MFASetupForm(FlaskForm):
    code = StringField('Código de verificação', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message='O código deve conter 6 dígitos')
    ])
