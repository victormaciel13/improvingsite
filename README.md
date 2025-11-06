# Ideal Empregos - Landing Page

Este projeto contém a landing page reformulada da Ideal Empregos com foco em profissionalismo, responsividade e interações modernas.

## Estrutura do projeto
- `index.html`: página principal.
- `assets/css/style.css`: estilos globais e componentes reutilizáveis.
- `assets/js/main.js`: comportamentos interativos.
- `tests/`: suíte de testes automatizados para validar a estrutura do site.
- `serve.py`: script para subir rapidamente um servidor local e visualizar o site.

## Recursos para candidatos
- Seção **Cadastre seu currículo** com formulário completo para envio de dados e currículo (PDF/DOC) diretamente para o banco de talentos.
- Área **Meu perfil** para visualizar rapidamente os dados salvos, atualizar contato, alterar preferências de alertas e substituir o currículo sem perder o histórico.
- Opção para optar pelo recebimento de alertas de novas vagas por e-mail e registro local das submissões para simular o fluxo de acompanhamento.
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

## Como executar os testes
Certifique-se de possuir o Python 3 instalado e execute:

```bash
python -m unittest discover tests
```

Os testes verificam se as seções principais estão presentes (incluindo a área de perfil), se os arquivos de estilos e scripts existem, se há um botão funcional de WhatsApp e se os formulários de cadastro e de edição mantêm os campos essenciais e restrições de arquivo.
