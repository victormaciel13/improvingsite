# Ideal Empregos - Landing Page

Este projeto contém a landing page reformulada da Ideal Empregos com foco em profissionalismo, responsividade e interações modernas.

## Estrutura do projeto
- `index.html`: tela de login exibida ao acessar o localhost, com aba dedicada para novos cadastros.
- `home.html`: landing page completa apresentada após a autenticação.
- `assets/css/style.css`: estilos globais e componentes reutilizáveis.
- `assets/js/main.js`: comportamentos interativos da landing page autenticada.
- `assets/js/login.js`: fluxo de autenticação, preenchimento automático e redirecionamento para a home.
- `tests/`: suíte de testes automatizados para validar a estrutura do site.
- `serve.py`: script para subir rapidamente um servidor local e visualizar o site.
- `storage.py`: camada de persistência responsável pelo banco de dados SQLite que armazena os cadastros.

## Recursos para candidatos
- **Tela de login dedicada** (`index.html`), isolada da landing page principal, com abas para login e cadastro e feedback imediato em cada envio.
- **Cadastro direto no login** para quem ainda não possui acesso, incluindo upload de currículo e consentimento para alertas antes de entrar na plataforma.
- **Landing page autenticada** (`home.html`) com seções completas de serviços, vagas, processos, blog e depoimentos para quem já fez login.
- **Botão oficial de WhatsApp (11 3539-1330)** fixo no cabeçalho das duas páginas para facilitar o contato com a equipe de atendimento.
- **Formulário “Cadastre seu currículo”** com upload de arquivos (PDF/DOC) e preferência por alertas por e-mail, alimentando diretamente o banco de dados SQLite.
- **Área “Meu perfil”** para revisar informações salvas, ajustar alertas, enviar um novo currículo e trocar a senha com regras mínimas de segurança.
- **Destaque automático de vagas** relacionadas à área do candidato autenticado, facilitando o início das candidaturas.
- **Mensagens de feedback acessíveis** em todos os formulários para orientar o usuário em casos de erro ou sucesso.

## Fluxo inicial de acesso
1. **Acesso ao login:** ao abrir `http://localhost:<porta>/` o usuário é direcionado para `index.html`, que exibe abas para entrar com uma conta existente ou criar um novo acesso.
2. **Cadastro de novos usuários:** selecionar a aba “Quero me cadastrar” envia os dados via `POST /api/candidates`, armazenando currículo, preferências de alertas e senha já na primeira experiência.
3. **Validação de credenciais:** quem já possui conta utiliza a aba de login, que dispara `POST /api/login`; em caso de sucesso o script salva o e-mail para preenchimento automático, registra o estado da sessão em `sessionStorage` e redireciona para `home.html`.
4. **Navegação autenticada:** a landing page exibe todas as seções e formulários apenas quando a sessão está autenticada. Caso a sessão expire ou seja limpa, qualquer tentativa de acessar `home.html` resulta em redirecionamento imediato para o login.
5. **Sessão persistida enquanto o navegador estiver aberto:** mantendo a aba ativa, o usuário pode atualizar a página ou navegar entre âncoras sem refazer o login.

## Como visualizar o site localmente
1. Garanta que você tenha o Python 3 instalado.
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
- Ao iniciar o servidor (`serve.py`), o projeto cria automaticamente o banco SQLite em `data/site.db` e armazena os currículos enviados em `data/uploads/`.
- Para alterar o diretório onde os dados são salvos, defina a variável de ambiente `IDEAL_DATA_DIR` antes de executar o servidor ou os testes.
- Cada submissão feita pelos formulários de cadastro ou de atualização de perfil cria ou atualiza um registro único identificado pelo e-mail do candidato.
- O formulário de cadastro solicita a criação de uma senha (mínimo de 6 caracteres) que é armazenada de forma criptografada para permitir o login posterior.
- O endpoint `POST /api/candidates` aceita tanto `multipart/form-data` (formulários com arquivo) quanto JSON e sempre retorna a representação persistida do candidato.
- O endpoint `GET /api/candidates/<email>` permite sincronizar o perfil já existente usando o próprio e-mail como chave.
- O endpoint `POST /api/login` valida credenciais (`email` + `senha`) e devolve os dados do candidato quando o login é bem-sucedido.

## Como usar o login e as recomendações
1. **Cadastro inicial:** utilize a aba “Quero me cadastrar” em `index.html` (ou a seção "Cadastre seu currículo" após o login) com nome, e-mail, área de interesse, currículo e uma senha com pelo menos 6 caracteres.
2. **Autenticação obrigatória:** sempre que acessar o localhost, informe o mesmo e-mail e senha em `index.html` para seguir para a landing page autenticada.
3. **Vagas em destaque:** após o login, a landing page destaca automaticamente os cards de vagas com a mesma área cadastrada, facilitando o acesso rápido às oportunidades relevantes.
4. **Atualizações de dados contínuas:** use a área **Meu perfil** para alterar informações, ativar/desativar alertas e enviar um novo currículo quando desejar. As alterações são persistidas no banco e refletem nas próximas sessões.

## Como executar os testes
Certifique-se de possuir o Python 3 instalado e execute:

```bash
python -m unittest discover tests
```

Os testes verificam se as seções principais da landing page autenticada permanecem disponíveis (cadastro, perfil, vagas, contato), se os arquivos de estilos e scripts existem (incluindo `assets/js/login.js`), se o cabeçalho mantém o botão oficial de WhatsApp e se todos os formulários preservam os campos obrigatórios e restrições de arquivo. A suíte também garante que a tela de login ofereça as abas de acesso e cadastro, além de cobrir a camada de persistência para assegurar o armazenamento consistente dos currículos no SQLite.
