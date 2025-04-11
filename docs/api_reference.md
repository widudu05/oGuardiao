# Documentação da API - O Guardião

## Visão Geral da API

A API do O Guardião permite que sistemas externos interajam com a plataforma para gerenciar certificados digitais, empresas e receber notificações sobre eventos importantes. Esta API segue os princípios RESTful e utiliza JSON para formatação de dados.

## Autenticação

Todas as requisições à API devem ser autenticadas utilizando um token JWT (JSON Web Token), obtido através do endpoint de autenticação.

### Obter Token

**Endpoint**: `/api/v1/auth/token`

**Método**: `POST`

**Parâmetros**:
```json
{
  "api_key": "sua_api_key",
  "api_secret": "seu_api_secret"
}
```

**Resposta**:
```json
{
  "access_token": "jwt_token",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Usar Token

Inclua o token em todas as requisições subsequentes no cabeçalho HTTP:

```
Authorization: Bearer jwt_token
```

## Endpoints

### Certificados

#### Listar Certificados

**Endpoint**: `/api/v1/certificates`

**Método**: `GET`

**Parâmetros de Consulta**:
- `company_id`: (opcional) Filtrar por empresa
- `type`: (opcional) Filtrar por tipo de certificado (e-cnpj, e-cpf)
- `expiring_in_days`: (opcional) Filtrar por certificados que expiram em X dias
- `page`: (opcional) Página para paginação (padrão: 1)
- `per_page`: (opcional) Itens por página (padrão: 20)

**Resposta**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Certificado ACME",
      "type": "e-cnpj",
      "company": {
        "id": 2,
        "name": "ACME Ltda",
        "cnpj": "00.000.000/0001-00"
      },
      "issue_date": "2023-01-01",
      "expiry_date": "2024-01-01",
      "created_at": "2023-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 42,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

#### Obter Detalhes do Certificado

**Endpoint**: `/api/v1/certificates/{certificate_id}`

**Método**: `GET`

**Resposta**:
```json
{
  "id": 1,
  "name": "Certificado ACME",
  "type": "e-cnpj",
  "company": {
    "id": 2,
    "name": "ACME Ltda",
    "cnpj": "00.000.000/0001-00"
  },
  "issue_date": "2023-01-01",
  "expiry_date": "2024-01-01",
  "created_by": {
    "id": 5,
    "name": "João Silva"
  },
  "created_at": "2023-01-01T10:00:00Z",
  "updated_at": "2023-01-01T10:00:00Z"
}
```

#### Upload de Certificado

**Endpoint**: `/api/v1/certificates`

**Método**: `POST`

**Conteúdo**: `multipart/form-data`

**Parâmetros**:
- `name`: Nome do certificado
- `type`: Tipo do certificado (e-cnpj, e-cpf)
- `company_id`: ID da empresa
- `certificate_file`: Arquivo do certificado (.pfx ou .p12)
- `password`: Senha do certificado
- `issue_date`: Data de emissão (YYYY-MM-DD)
- `expiry_date`: Data de validade (YYYY-MM-DD)

**Resposta**:
```json
{
  "id": 1,
  "name": "Certificado ACME",
  "type": "e-cnpj",
  "company_id": 2,
  "issue_date": "2023-01-01",
  "expiry_date": "2024-01-01",
  "created_at": "2023-01-01T10:00:00Z",
  "message": "Certificado carregado com sucesso"
}
```

#### Excluir Certificado

**Endpoint**: `/api/v1/certificates/{certificate_id}`

**Método**: `DELETE`

**Resposta**:
```json
{
  "message": "Certificado excluído com sucesso"
}
```

### Empresas

#### Listar Empresas

**Endpoint**: `/api/v1/companies`

**Método**: `GET`

**Parâmetros de Consulta**:
- `group_id`: (opcional) Filtrar por grupo
- `search`: (opcional) Buscar por nome ou CNPJ
- `page`: (opcional) Página para paginação
- `per_page`: (opcional) Itens por página

**Resposta**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "ACME Ltda",
      "trade_name": "ACME",
      "cnpj": "00.000.000/0001-00",
      "group": {
        "id": 3,
        "name": "Grupo A"
      },
      "certificates_count": 5
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

#### Obter Detalhes da Empresa

**Endpoint**: `/api/v1/companies/{company_id}`

**Método**: `GET`

**Resposta**:
```json
{
  "id": 1,
  "name": "ACME Ltda",
  "trade_name": "ACME",
  "cnpj": "00.000.000/0001-00",
  "group": {
    "id": 3,
    "name": "Grupo A"
  },
  "certificates": [
    {
      "id": 1,
      "name": "Certificado ACME",
      "type": "e-cnpj",
      "expiry_date": "2024-01-01"
    }
  ],
  "created_at": "2022-01-01T10:00:00Z",
  "updated_at": "2022-01-01T10:00:00Z"
}
```

#### Criar Empresa

**Endpoint**: `/api/v1/companies`

**Método**: `POST`

**Parâmetros**:
```json
{
  "name": "ACME Ltda",
  "trade_name": "ACME",
  "cnpj": "00.000.000/0001-00",
  "group_id": 3
}
```

**Resposta**:
```json
{
  "id": 1,
  "name": "ACME Ltda",
  "trade_name": "ACME",
  "cnpj": "00.000.000/0001-00",
  "group_id": 3,
  "created_at": "2023-01-01T10:00:00Z",
  "message": "Empresa criada com sucesso"
}
```

#### Atualizar Empresa

**Endpoint**: `/api/v1/companies/{company_id}`

**Método**: `PUT`

**Parâmetros**:
```json
{
  "name": "ACME Ltda (atualizado)",
  "trade_name": "ACME",
  "cnpj": "00.000.000/0001-00",
  "group_id": 4
}
```

**Resposta**:
```json
{
  "id": 1,
  "name": "ACME Ltda (atualizado)",
  "trade_name": "ACME",
  "cnpj": "00.000.000/0001-00",
  "group_id": 4,
  "updated_at": "2023-01-02T10:00:00Z",
  "message": "Empresa atualizada com sucesso"
}
```

#### Excluir Empresa

**Endpoint**: `/api/v1/companies/{company_id}`

**Método**: `DELETE`

**Resposta**:
```json
{
  "message": "Empresa excluída com sucesso"
}
```

### Webhooks

A API suporta webhooks para notificar sistemas externos sobre eventos importantes.

#### Configurar Webhook

**Endpoint**: `/api/v1/webhooks`

**Método**: `POST`

**Parâmetros**:
```json
{
  "url": "https://seu-sistema.com/webhook",
  "events": ["certificate.expiring", "certificate.uploaded"],
  "secret": "seu_webhook_secret"
}
```

**Resposta**:
```json
{
  "id": 1,
  "url": "https://seu-sistema.com/webhook",
  "events": ["certificate.expiring", "certificate.uploaded"],
  "created_at": "2023-01-01T10:00:00Z",
  "message": "Webhook configurado com sucesso"
}
```

#### Listar Webhooks

**Endpoint**: `/api/v1/webhooks`

**Método**: `GET`

**Resposta**:
```json
{
  "data": [
    {
      "id": 1,
      "url": "https://seu-sistema.com/webhook",
      "events": ["certificate.expiring", "certificate.uploaded"],
      "created_at": "2023-01-01T10:00:00Z"
    }
  ]
}
```

#### Excluir Webhook

**Endpoint**: `/api/v1/webhooks/{webhook_id}`

**Método**: `DELETE`

**Resposta**:
```json
{
  "message": "Webhook excluído com sucesso"
}
```

## Formato dos Webhooks

Quando um evento ocorre, o sistema envia uma requisição POST para a URL configurada com os seguintes dados:

```json
{
  "event": "certificate.expiring",
  "timestamp": "2023-01-01T10:00:00Z",
  "data": {
    "certificate_id": 1,
    "name": "Certificado ACME",
    "type": "e-cnpj",
    "company_id": 2,
    "company_name": "ACME Ltda",
    "expiry_date": "2024-01-01",
    "days_remaining": 15
  }
}
```

A autenticidade da mensagem pode ser verificada usando o cabeçalho `X-Guardiao-Signature`, que contém uma assinatura HMAC-SHA256 do corpo da requisição usando o secret configurado.

## Códigos de Status

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Parâmetros inválidos
- `401 Unauthorized`: Autenticação inválida
- `403 Forbidden`: Sem permissão para acessar o recurso
- `404 Not Found`: Recurso não encontrado
- `422 Unprocessable Entity`: Dados enviados são inválidos
- `429 Too Many Requests`: Limite de requisições excedido
- `500 Internal Server Error`: Erro interno do servidor

## Limites de Requisição

A API impõe um limite de 100 requisições por minuto por API key. As requisições que excedem esse limite receberão o status 429. O limite restante é informado nos cabeçalhos:

- `X-RateLimit-Limit`: Limite total de requisições
- `X-RateLimit-Remaining`: Requisições restantes
- `X-RateLimit-Reset`: Timestamp Unix de quando o limite será reiniciado