# Arquitetura - O Guardião

## Diagrama de Arquitetura

```
+------------------------+     +------------------------+
|                        |     |                        |
|    Cliente Web         |     |    Cliente Mobile      |
|    (Browser)           |     |    (Futuro)            |
|                        |     |                        |
+----------+-------------+     +-------------+----------+
           |                                 |
           |                                 |
           v                                 v
+----------+-------------+     +-------------+----------+
|                        |     |                        |
|  API Gateway           |     |  API RESTful           |
|  (Futuro)              +---->+  (Flask)               |
|                        |     |                        |
+----------+-------------+     +-------------+----------+
           ^                                 ^
           |                                 |
           v                                 v
+----------+-------------+     +-------------+----------+     +-------------------------+
|                        |     |                        |     |                         |
|  Aplicação Flask       |     |  Camada de Serviços    |     |  Sistema de Autenticação|
|  - Controllers         +---->+  - CertificateService  +---->+  - Login                |
|  - Routes              |     |  - CompanyService      |     |  - MFA                  |
|  - Templates           |     |  - UserService         |     |  - RBAC                 |
|                        |     |                        |     |                         |
+----------+-------------+     +-------------+----------+     +------------+------------+
           |                                 |                              |
           |                                 |                              |
           v                                 v                              v
+----------+----------------------------------------------------------+----+-------+
|                                                                     |            |
|  Camada de Persistência                                             |            |
|  - SQLAlchemy ORM                                                   |            |
|  - Models                                                           |            |
|                                                                     |            |
+----------+------------------------------+----------------------------+            |
           |                              |                                         |
           v                              v                                         |
+----------+-------------+   +------------+-----------+                             |
|                        |   |                        |                             |
|  Banco de Dados        |   |  Armazenamento de      |                             |
|  PostgreSQL            |   |  Arquivos (S3)         |                             |
|                        |   |                        |                             |
+------------------------+   +------------------------+                             |
                                                                                    |
                                                                                    |
+----------+-------------+   +------------------------+                             |
|                        |   |                        |                             |
|  Serviço de Email      |   |  Sistema de Logs e     +-----------------------------+
|  SMTP                  |   |  Auditoria             |
|                        |   |                        |
+------------------------+   +------------------------+

```

## Integrações Externas (Planejadas)

```
                          +------------------------+
                          |                        |
                          |      O Guardião        |
                          |                        |
                          +-+--------+--------+----+
                            |        |        |
                            |        |        |
           +----------------v-+    +-v--------v--+    +----------------+
           |                  |    |             |    |                |
           |    SafeID        |    |  Valid Cloud|    |   Sistemas     |
           |    - Validação   |    |  - Emissão  |    |   Externos     |
           |    - Revogação   |    |  - Renovação|    |   (via API)    |
           |                  |    |             |    |                |
           +------------------+    +-------------+    +----------------+

```

## Fluxo de Dados

### Upload de Certificado
```
[Cliente Web] → [Controller] → [CertificateService] → 
  → Criptografia da senha → 
  → Upload para S3 → 
  → Registro no PostgreSQL → 
  → [Cliente Web]
```

### Alerta de Expiração
```
[Tarefa Agendada] → [CertificateService] → 
  → Verificar certificados expirando → 
  → Criar alertas no sistema →
  → Enviar notificações por email →
  → Registrar na auditoria
```

### Login com MFA
```
[Cliente Web] → [AuthController] → 
  → Validar credenciais → 
  → Solicitar código MFA → 
  → [Cliente Web] → 
  → Enviar código MFA → 
  → [AuthController] → 
  → Validar código → 
  → Criar sessão → 
  → Registrar na auditoria →
  → [Cliente Web]
```

## Componentes Principais

### Backend (Flask)
- **Controllers**: Gerenciam as requisições HTTP
- **Services**: Contêm a lógica de negócio
- **Models**: Definem a estrutura dos dados
- **Utils**: Funções utilitárias (criptografia, geração de tokens, etc.)

### Frontend
- **Templates**: Renderizados via Jinja2
- **Static Assets**: CSS, JavaScript, imagens
- **Client Scripts**: Interação dinâmica via JavaScript

### Banco de Dados
- **PostgreSQL**: Armazenamento relacional para todos os dados
- **SQLAlchemy**: ORM para interação com o banco de dados

### Armazenamento
- **AWS S3**: Armazenamento seguro de certificados
- **Criptografia**: Proteção de senhas com AES-256

### Outros Serviços
- **Email**: Envio de notificações via SMTP
- **Logs**: Auditoria de todas as ações no sistema
- **MFA**: Autenticação de dois fatores via TOTP