# Documentação - O Guardião

Bem-vindo à documentação completa do sistema O Guardião, uma plataforma SaaS para gerenciamento seguro de certificados digitais.

## Índice de Documentos

### Documentação Técnica
- [Documentação Técnica](documentacao_tecnica.md) - Visão geral técnica do sistema, arquitetura e componentes principais
- [Arquitetura](arquitetura.md) - Diagramas e fluxos da arquitetura do sistema
- [API Reference](api_reference.md) - Documentação completa da API RESTful

### Guias e Manuais
- [Guia de Instalação](instalacao.md) - Instruções detalhadas para instalação e configuração do sistema

### Roadmap e Planejamento
- [Roadmap](roadmap.md) - Planejamento de futuras versões e funcionalidades

## Sobre O Guardião

O Guardião é uma plataforma SaaS (Software as a Service) desenvolvida para gerenciar de forma segura o ciclo de vida de certificados digitais. A plataforma permite que empresas gerenciem seus certificados em um ambiente centralizado, com controles avançados de segurança e alertas de expiração.

### Principais Funcionalidades

- **Gestão de Certificados**: Upload, armazenamento seguro e visualização de certificados digitais
- **Alertas de Expiração**: Notificações automáticas para certificados próximos ao vencimento
- **Controle de Acesso**: Sistema de permissões baseado em papéis (master admin, admin, operador)
- **Autenticação Segura**: Sistema de autenticação com MFA (Multi-Factor Authentication)
- **Organização Hierárquica**: Gestão de empresas e grupos para organização eficiente dos certificados
- **Auditoria**: Registro detalhado de todas as atividades realizadas na plataforma

### Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Segurança**: Flask-Login, autenticação em dois fatores

### Integrações Planejadas

- **SafeID**: Para validação de certificados
- **Valid Cloud**: Para emissão e renovação de certificados
- **Assinatura Digital**: Para assinar documentos com certificados
- **API Pública**: Para integração com sistemas externos

## Contribuição

O Guardião é um projeto proprietário. Para contribuir, entre em contato com a equipe de desenvolvimento.

## Suporte

Para suporte técnico, entre em contato através do email suporte@oguardiao.com.br