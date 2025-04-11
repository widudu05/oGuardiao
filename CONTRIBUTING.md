# Guia de Contribuição - O Guardião

Obrigado pelo interesse em contribuir com o projeto O Guardião! Este documento fornece orientações para o processo de contribuição.

## Fluxo de Trabalho

1. Faça um fork do repositório
2. Clone o seu fork: `git clone https://github.com/SEU_USUARIO/oGuardiao.git`
3. Adicione o repositório original como upstream: `git remote add upstream https://github.com/widudu05/oGuardiao.git`
4. Crie uma branch para sua feature: `git checkout -b feature/nome-da-feature`
5. Faça suas alterações e commit: `git commit -am 'Adiciona nova feature'`
6. Mantenha sua branch atualizada: `git pull upstream main`
7. Faça push para o seu fork: `git push origin feature/nome-da-feature`
8. Crie um Pull Request para a branch main do repositório original

## Padrões de Código

- Siga a PEP 8 para código Python
- Use docstrings para documentar funções e classes
- Escreva testes para novas funcionalidades

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
├── static/                # Arquivos estáticos
├── templates/             # Templates Jinja2
└── docs/                  # Documentação
```

## Convenções de Commit

Utilize mensagens de commit claras e descritivas, iniciando com um verbo no imperativo:

- `Add`: para novas funcionalidades
- `Fix`: para correções de bugs
- `Update`: para atualizações em recursos existentes
- `Refactor`: para refatorações de código
- `Docs`: para atualizações na documentação
- `Test`: para adição ou modificação de testes
- `Chore`: para tarefas de manutenção

Exemplo: `Add certificate expiration notification system`

## Testes

Antes de submeter um PR, certifique-se de que:

1. Todos os testes estão passando: `python -m pytest`
2. Você adicionou testes para novas funcionalidades
3. A aplicação está funcionando como esperado

## Documentação

Ao adicionar novas funcionalidades, atualize a documentação correspondente:

- Atualize os arquivos na pasta `docs/`
- Adicione comentários relevantes no código
- Atualize o README.md se necessário

## Segurança

Tratando-se de uma aplicação que lida com certificados digitais, a segurança é crítica:

- Nunca comite credenciais ou tokens
- Utilize as práticas de segurança recomendadas para Flask
- Esteja atento a vulnerabilidades em dependências

## Processo de Review

Cada Pull Request será revisado pela equipe mantenedora. O processo pode incluir:

1. Verificação automatizada de estilo e testes
2. Review de código
3. Discussão de design e arquitetura
4. Solicitação de alterações quando necessário

## Licença

Ao contribuir com o projeto, você concorda que suas contribuições serão licenciadas sob a mesma licença do projeto.

## Contato

Se você tiver dúvidas sobre o processo de contribuição, entre em contato através do email desenvolvimento@oguardiao.com.br