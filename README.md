# Ideal Empregos - Landing Page

Este projeto contém a landing page reformulada da Ideal Empregos com foco em profissionalismo, responsividade e interações modernas.

## Estrutura do projeto
- `index.html`: página principal.
- `assets/css/style.css`: estilos globais e componentes reutilizáveis.
- `assets/js/main.js`: comportamentos interativos.
- `tests/`: suíte de testes automatizados para validar a estrutura do site.
- `serve.py`: script para subir rapidamente um servidor local e visualizar o site.
- `storage.py`: camada de persistência responsável pelo banco de dados SQLite que armazena os cadastros.

## Recursos para candidatos
- Seção **Cadastre seu currículo** com formulário completo para envio de dados e currículo (PDF/DOC) diretamente para o banco de talentos.
- Área **Login** para que candidatos cadastrados acessem o perfil com e-mail e senha e visualizem recomendações instantâneas.
- Área **Meu perfil** para visualizar rapidamente os dados salvos, atualizar contato, alterar preferências de alertas e substituir o currículo sem perder o histórico.
- Opção para optar pelo recebimento de alertas de novas vagas por e-mail com armazenamento real dos cadastros no banco de dados.
- Feedback imediato após o envio com orientações claras em caso de campos faltantes e mensagens de sucesso acessíveis.

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
1. **Cadastro inicial:** preencha o formulário "Cadastre seu currículo" informando nome, e-mail, área de interesse, currículo e defina uma senha com pelo menos 6 caracteres.
2. **Acesso ao perfil:** utilize a seção de **Login** para entrar com o mesmo e-mail e senha; após a autenticação as informações do perfil são carregadas automaticamente.
3. **Recomendações personalizadas:** ao entrar, as vagas que combinam com a área de interesse cadastrada ganham destaque visual e são listadas na própria seção de login.
4. **Atualizações de dados:** na área **Meu perfil** é possível alterar dados, preferências e, se desejar, definir uma nova senha (opcional) sempre respeitando o mínimo de 6 caracteres.

## Como executar os testes
Certifique-se de possuir o Python 3 instalado e execute:

```bash
python -m unittest discover tests
```

Os testes verificam se as seções principais estão presentes (incluindo a área de perfil), se os arquivos de estilos e scripts existem, se o botão principal do cabeçalho direciona para a área de cadastro e se os formulários de cadastro e de edição mantêm os campos essenciais e restrições de arquivo. A suíte também cobre a camada de persistência, garantindo que os cadastros sejam armazenados corretamente no banco de dados SQLite e que atualizações mantenham o histórico do currículo.
