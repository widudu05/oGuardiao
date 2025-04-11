# O Guardião

O Guardião é uma plataforma SaaS (Software as a Service) para gerenciamento seguro de certificados digitais, fornecendo uma solução completa para o ciclo de vida dos certificados.

## Funcionalidades

- **Gestão de Certificados**: Upload, armazenamento seguro e visualização de certificados digitais
- **Alertas de Expiração**: Notificações automáticas para certificados próximos ao vencimento
- **Controle de Acesso**: Sistema de permissões baseado em papéis (master admin, admin, operador)
- **Autenticação Segura**: Sistema de autenticação com MFA (Multi-Factor Authentication)
- **Organização Hierárquica**: Gestão de empresas e grupos para organização eficiente dos certificados
- **Auditoria**: Registro detalhado de todas as atividades realizadas na plataforma

## Integração

O sistema prepara-se para integrar com:

- SafeID
- Valid Cloud
- Assinatura digital
- API pública com webhooks

## Tecnologias

- **Backend**: Flask (Python)
- **Banco de Dados**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Segurança**: Flask-Login, autenticação em dois fatores

## Instalação

1. Clone o repositório
```
git clone https://github.com/widudu05/oGuardiao.git
```

2. Instale as dependências
```
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`

4. Execute as migrações do banco de dados
```
flask db upgrade
```

5. Inicie o servidor
```
gunicorn --bind 0.0.0.0:5000 main:app
```

## Licença

Este projeto está sob licença proprietária. Todos os direitos reservados.