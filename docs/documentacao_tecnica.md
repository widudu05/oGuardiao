# Documentação Técnica - O Guardião

## Visão Geral da Arquitetura

O Guardião é uma plataforma SaaS desenvolvida com arquitetura MVC (Model-View-Controller) utilizando o framework Flask. A aplicação é projetada para permitir gerenciamento seguro de certificados digitais, com foco em segurança, escalabilidade e facilidade de uso.

### Componentes Principais

1. **Backend**: Flask (Python)
2. **Frontend**: HTML, CSS, JavaScript (com bibliotecas jQuery e Chart.js)
3. **Banco de Dados**: PostgreSQL
4. **Armazenamento**: AWS S3 (para certificados)
5. **Email**: SMTP (para notificações)
6. **Autenticação**: Sistema próprio com MFA via TOTP (Time-based One-Time Password)
7. **Segurança**: Criptografia AES-256 para senhas de certificados

## Estrutura do Projeto

```
oGuardiao/
├── app.py                 # Configuração principal da aplicação
├── main.py                # Ponto de entrada da aplicação
├── auth.py                # Rotas e lógica de autenticação
├── routes.py              # Rotas gerais da aplicação
├── forms.py               # Formulários WTForms
├── models.py              # Modelos do banco de dados
├── utils.py               # Funções utilitárias
├── config.py              # Configurações
├── static/                # Arquivos estáticos (CSS, JS, imagens)
│   ├── css/               # Folhas de estilo
│   ├── js/                # Scripts JavaScript
│   └── img/               # Imagens
├── templates/             # Templates Jinja2
│   ├── emails/            # Templates de email
│   ├── companies/         # Templates de empresas
│   └── certificates/      # Templates de certificados
└── docs/                  # Documentação
```

## Modelos de Dados

### User
- **Responsabilidade**: Gerenciar usuários e autenticação
- **Atributos principais**: id, name, email, password_hash, role, organization_id, mfa_secret, mfa_enabled
- **Relacionamentos**: pertence a uma Organization, possui vários AuditLog

### Organization
- **Responsabilidade**: Representar organizações clientes
- **Atributos principais**: id, name, plan, cnpj, responsible
- **Relacionamentos**: possui vários User, Company e Group

### Group
- **Responsabilidade**: Agrupar empresas para melhor organização
- **Atributos principais**: id, name, description, organization_id
- **Relacionamentos**: pertence a uma Organization, possui várias Company

### Company
- **Responsabilidade**: Armazenar informações de empresas
- **Atributos principais**: id, name, trade_name, cnpj, organization_id, group_id
- **Relacionamentos**: pertence a uma Organization e opcionalmente a um Group, possui vários Certificate

### Certificate
- **Responsabilidade**: Armazenar informações e arquivos de certificados digitais
- **Atributos principais**: id, name, type, file_name, encrypted_password, iv, s3_key, company_id, issue_date, expiry_date, created_by
- **Relacionamentos**: pertence a uma Company, criado por um User

### AuditLog
- **Responsabilidade**: Registrar todas as atividades do sistema para auditoria
- **Atributos principais**: id, action, details, ip_address, user_id, created_at
- **Relacionamentos**: pertence a um User

### UserInvite
- **Responsabilidade**: Gerenciar convites para novos usuários
- **Atributos principais**: id, email, token, organization_id, role, invited_by, accepted, expires_at
- **Relacionamentos**: pertence a uma Organization, criado por um User

## Fluxos Principais

### Autenticação
1. Login via email/senha
2. Verificação MFA (se habilitado)
3. Redirecionamento para dashboard

### Gestão de Certificados
1. Upload de certificado com senha
2. Criptografia da senha do certificado
3. Armazenamento do arquivo no S3
4. Registro de metadados no banco de dados

### Alertas de Expiração
1. Verificação diária de certificados próximos ao vencimento
2. Geração de alertas no sistema
3. Envio de notificações por email

## Segurança

### Autenticação
- Senhas armazenadas com hash (Werkzeug)
- Autenticação de dois fatores (MFA) via TOTP
- Tokens de sessão seguros com Flask-Login

### Proteção de Dados
- Senhas de certificados criptografadas com AES-256
- Transmissão de dados via HTTPS
- Sanitização de inputs com WTForms
- Proteção contra CSRF com Flask-WTF

### Controle de Acesso
- Sistema de permissões baseado em papéis:
  - **master_admin**: acesso total à organização
  - **admin**: gerenciamento de certificados e empresas
  - **operator**: visualização e uso básico

## Integrações

### Atuais
- AWS S3 para armazenamento de certificados
- SMTP para envio de emails

### Planejadas
- SafeID: para validação de certificados
- Valid Cloud: para integração com serviços da Valid
- API pública: para integração com sistemas externos
- Webhooks: para notificações em tempo real

## Monitoramento e Logs

- Logs de aplicação via Python logging
- Logs de auditoria no banco de dados (AuditLog)
- Rastreamento de atividades dos usuários

## Backup e Recuperação

- Backup diário do banco de dados
- Versionamento dos certificados no S3
- Procedimentos de recuperação documentados

## Escalabilidade

- Arquitetura stateless para suporte a múltiplas instâncias
- Uso de PostgreSQL para persistência de dados confiável
- Projeto preparado para balanceamento de carga

## Considerações de Manutenção

- Atualizações de dependências devem ser testadas em ambiente de homologação
- Migrações de banco de dados devem ser versionadas
- Testes automatizados devem ser mantidos e expandidos

## Requisitos do Sistema

- Python 3.9+
- PostgreSQL 13+
- Servidor web com suporte a WSGI
- Acesso à internet para integração com S3 e envio de emails