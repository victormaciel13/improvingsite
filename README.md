# Ideal Empregos - Landing Page

Este projeto contém a landing page reformulada da Ideal Empregos com foco em profissionalismo, responsividade e interações modernas.

## Estrutura do projeto
- `index.html`: tela de login exibida ao acessar o localhost, com aba dedicada para novos cadastros.
- `home.html`: landing page completa apresentada após a autenticação.
- `cadastro.html`: página dedicada para inscrição no banco de talentos após o login.
- `perfil.html`: página exclusiva para revisar e atualizar um cadastro existente.
- `admin.html`: painel restrito para revisar candidaturas, aceitar ou recusar perfis e acompanhar totais por vaga.
- `assets/css/style.css`: estilos globais e componentes reutilizáveis.
- `assets/js/main.js`: comportamentos interativos da landing page autenticada.
- `assets/js/login.js`: fluxo de autenticação, preenchimento automático e redirecionamento para a home.
- `assets/js/admin.js`: autenticação administrativa e operações de revisão de candidaturas.
- `tests/`: suíte de testes automatizados para validar a estrutura do site.
- `serve.py`: script para subir rapidamente um servidor local e visualizar o site.
- `storage.py`: camada de persistência responsável pelo banco de dados SQLite que armazena os cadastros.

## Recursos para candidatos
- **Tela de login dedicada** (`index.html`), isolada da landing page principal, com abas para login e cadastro e feedback imediato em cada envio.
- **Cadastro direto no login** para quem ainda não possui acesso, incluindo upload de currículo e consentimento para alertas antes de entrar na plataforma.
- **Landing page autenticada** (`home.html`) com seções completas de serviços, vagas, processos, blog e depoimentos para quem já fez login.
- **Botão oficial de WhatsApp (11 3539-1330)** fixo no cabeçalho das duas páginas para facilitar o contato com a equipe de atendimento.
- **Página “Cadastre seu currículo”** (`cadastro.html`) com upload de arquivos (PDF/DOC), definição de senha e preferência por alertas por e-mail, alimentando diretamente o banco de dados SQLite.
- **Página “Atualize seu cadastro”** (`perfil.html`) para revisar informações salvas, ajustar alertas, enviar um novo currículo e trocar a senha com regras mínimas de segurança.
- **Painel do administrador** (`admin.html`) para acompanhar todos os processos seletivos, contabilizar inscritos por vaga e aceitar ou recusar candidatos autenticados.
- **Destaque automático de vagas** relacionadas à área do candidato autenticado, facilitando o início das candidaturas.
- **Mensagens de feedback acessíveis** em todos os formulários para orientar o usuário em casos de erro ou sucesso.
- **Assistente virtual** com chat fixo no canto inferior direito oferecendo respostas rápidas sobre cadastro, vagas e canais de atendimento.

## Fluxo inicial de acesso
1. **Acesso ao login:** ao abrir `http://localhost:<porta>/` o usuário é direcionado para `index.html`, que exibe abas para entrar com uma conta existente ou criar um novo acesso.
2. **Cadastro de novos usuários:** selecionar a aba “Quero me cadastrar” envia os dados via `POST /api/candidates`, armazenando currículo, preferências de alertas e senha já na primeira experiência.
3. **Validação de credenciais:** quem já possui conta utiliza a aba de login, que dispara `POST /api/login`; em caso de sucesso o script salva o e-mail para preenchimento automático, registra o estado da sessão em `sessionStorage` e redireciona para `home.html`.
4. **Navegação autenticada:** a landing page exibe todas as seções e formulários apenas quando a sessão está autenticada. Caso a sessão expire ou seja limpa, qualquer tentativa de acessar `home.html` resulta em redirecionamento imediato para o login.
5. **Sessão persistida enquanto o navegador estiver aberto:** mantendo a aba ativa, o usuário pode atualizar a página ou navegar entre âncoras sem refazer o login.

## Como visualizar o site localmente
1. Garanta que você tenha o Python 3 instalado e as dependências do projeto:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. No diretório do projeto, execute:

   ```bash
   python serve.py
   ```

   O script tentará usar a porta `8000` (ou a primeira disponível) e abrirá o navegador automaticamente. Use `Ctrl+C` para encerrar.

   Para escolher outra porta ou impedir a abertura automática do navegador, utilize:

   ```bash
   python serve.py --port 8080 --no-browser
  ```

## Banco de dados e armazenamento de currículos
- Ao iniciar o servidor (`serve.py`), o projeto cria automaticamente o banco SQLite em `data/site.db` e armazena os currículos enviados em `data/uploads/` (ambos são criados se ainda não existirem).
- Para alterar o diretório onde os dados são salvos, defina a variável de ambiente `IDEAL_DATA_DIR` antes de executar o servidor ou os testes.
- Cada submissão feita pelos formulários de cadastro ou de atualização de perfil cria ou atualiza um registro único identificado pelo e-mail do candidato e sincroniza os arquivos no diretório `data/uploads/`.
- Todas as senhas são convertidas em hash usando `bcrypt` (com custo padrão seguro) antes de serem persistidas, garantindo que nenhuma credencial fique em texto puro no disco. Caso a dependência não esteja disponível, o sistema recorre automaticamente a um hash PBKDF2 (SHA-256) igualmente seguro e compatível com os registros existentes.
- Colunas e campos principais da tabela `candidates`:
  - `nome`, `email` (único), `area_interesse`, `telefone`
  - `recebe_alertas` (0/1), `curriculo_path`, `senha_hash`
  - `criado_em` e `atualizado_em` (com `CURRENT_TIMESTAMP` no SQLite)

## API disponível
- `POST /api/candidates`
  - Aceita `multipart/form-data` (para formulários com currículo) **ou** JSON (`application/json`).
  - Se o e-mail ainda não existe, cria um registro exigindo senha; caso contrário, atualiza os campos enviados (senha só é atualizada quando fornecida).
  - Sempre retorna `{ "candidate": { ... } }` com `areaInteresse`, `recebeAlertas`, caminho do currículo e metadados de criação/atualização.
- `GET /api/candidates/<email>`
  - Retorna os dados completos do candidato para preencher os formulários de revisão.
  - Responde com `404` caso o e-mail não esteja cadastrado.
- `POST /api/login`
  - Recebe JSON com `email` e `senha`.
  - Em caso de sucesso devolve `{ "candidate": { ... } }` com nome e área de interesse, permitindo que o front-end registre a sessão.
  - Retorna `401` se as credenciais estiverem incorretas e `400` quando o payload estiver incompleto.
- `POST /api/applications`
  - Recebe JSON com `email`, `jobId` e `jobTitle` enviados pela página autenticada.
  - Registra ou atualiza a candidatura no banco, mantendo o status inicial como `em_analise`.
- `GET /api/admin/applications`
  - Requer cabeçalho `X-Admin-Token` obtido após login de administrador e retorna a lista de candidaturas com resumo por vaga.
- `POST /api/admin/applications/<id>/status`
  - Requer `X-Admin-Token` e JSON `{ "status": "aceito" | "recusado" | "em_analise" }` para atualizar o processo.

## Integração front-end com a API
- O `login.js` envia as credenciais para `/api/login`, salva o e-mail mais recente em `localStorage` (auto preenchimento) e registra o objeto `idealSessionUser` em `sessionStorage` com `email`, `nome` e `areaInteresse`. Esse objeto é consumido pelas demais páginas para garantir que apenas usuários autenticados avancem para `home.html`, `cadastro.html` e `perfil.html`.
- O mesmo script utiliza `POST /api/candidates` para o cadastro inicial direto no login, sincronizando imediatamente o banco local com o formulário recém-enviado.
- O `main.js` (carregado após o login) consulta `sessionStorage` para confirmar a autenticidade da sessão e recuperar a área de interesse salva. Caso não exista sessão válida, o usuário é redirecionado de volta para `index.html`.
- Páginas autenticadas:
  - **`home.html`** destaca automaticamente os cards de vagas cuja `data-area` coincide com `areaInteresse` do usuário carregado em `sessionStorage`/`localStorage`.
  - **`cadastro.html`** e **`perfil.html`** reaproveitam o mesmo endpoint `POST /api/candidates` para criar/atualizar registros, exibem mensagens de sucesso/erro e mantêm os campos de e-mail preenchidos com base na sessão ativa.
  - **`perfil.html`** utiliza `GET /api/candidates/<email>` ao carregar para apresentar o resumo salvo, permitir upload opcional de um novo currículo e sincronizar os alertas de vagas.
- Em todos os formulários, o feedback visual informa quando o currículo está “em análise”, quando alertas estão ativos e quando uma senha precisa ser reajustada.
- O painel administrativo (`admin.html`) utiliza `/api/login` com conta privilegiada (variáveis `IDEAL_ADMIN_EMAIL` e `IDEAL_ADMIN_PASSWORD`, padrões `admin@idealempregos.test`/`admin123`) e, após autenticado, consulta `/api/admin/applications` para exibir totalizadores e permite atualizar status via `/api/admin/applications/<id>/status`.

## Como usar o login e as recomendações
1. **Cadastro inicial:** utilize a aba “Quero me cadastrar” em `index.html` (ou, após autenticar-se, abra a página "Cadastre seu currículo" pelo menu principal) com nome, e-mail, área de interesse, currículo e uma senha com pelo menos 6 caracteres.
2. **Autenticação obrigatória:** sempre que acessar o localhost, informe o mesmo e-mail e senha em `index.html` para seguir para a landing page autenticada.
3. **Vagas em destaque:** após o login, a landing page destaca automaticamente os cards de vagas com a mesma área cadastrada, facilitando o acesso rápido às oportunidades relevantes.
4. **Atualizações de dados contínuas:** use a página **Atualize seu cadastro** para alterar informações, ativar/desativar alertas e enviar um novo currículo quando desejar. As alterações são persistidas no banco e refletem nas próximas sessões.

## Como executar os testes
Certifique-se de possuir o Python 3 instalado e execute:

```bash
python -m unittest discover tests
```

Os testes verificam se as seções principais da landing page autenticada permanecem disponíveis (vagas, processo, contato, assistente virtual), se o menu aponta corretamente para as páginas dedicadas `cadastro.html` e `perfil.html`, se os arquivos de estilos e scripts existem (incluindo `assets/js/login.js`) e se os formulários obrigatórios nas páginas de cadastro e atualização preservam campos e validações. A suíte também garante que a tela de login ofereça as abas de acesso e cadastro, valida o botão oficial de WhatsApp no cabeçalho e cobre a camada de persistência para assegurar o armazenamento consistente dos currículos no SQLite.
