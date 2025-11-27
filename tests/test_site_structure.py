import re
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HOME_PATH = BASE_DIR / "home.html"
LOGIN_PATH = BASE_DIR / "index.html"
CADASTRO_PATH = BASE_DIR / "cadastro.html"
PERFIL_PATH = BASE_DIR / "perfil.html"
ADMIN_PATH = BASE_DIR / "admin.html"
CSS_PATH = BASE_DIR / "assets" / "css" / "style.css"
MAIN_JS_PATH = BASE_DIR / "assets" / "js" / "main.js"
LOGIN_JS_PATH = BASE_DIR / "assets" / "js" / "login.js"
ADMIN_JS_PATH = BASE_DIR / "assets" / "js" / "admin.js"

HOME_CONTENT = HOME_PATH.read_text(encoding="utf-8")
LOGIN_CONTENT = LOGIN_PATH.read_text(encoding="utf-8")
CADASTRO_CONTENT = CADASTRO_PATH.read_text(encoding="utf-8")
PERFIL_CONTENT = PERFIL_PATH.read_text(encoding="utf-8")
ADMIN_CONTENT = ADMIN_PATH.read_text(encoding="utf-8")


class TestSiteStructure(unittest.TestCase):
    def test_source_files_without_merge_conflicts(self):
        merge_markers = ("<<<<<<<", "=======", ">>>>>>>")
        tracked_files = [
            HOME_PATH,
            LOGIN_PATH,
            CADASTRO_PATH,
            PERFIL_PATH,
            ADMIN_PATH,
            CSS_PATH,
            MAIN_JS_PATH,
            LOGIN_JS_PATH,
            ADMIN_JS_PATH,
            BASE_DIR / "README.md",
            BASE_DIR / "serve.py",
        ]

        for file_path in tracked_files:
            with self.subTest(file=file_path.name):
                content = file_path.read_text(encoding="utf-8")
                for marker in merge_markers:
                    self.assertNotIn(
                        marker,
                        content,
                        msg=(
                            f"O arquivo {file_path.name} contém marcadores de conflito de merge. "
                            "Resolva os conflitos antes de executar os testes."
                        ),
                    )

    def test_home_sections_present(self):
        selectors = {
            "hero": r'class=\"hero\"',
            "sobre": r'id=\"sobre\"',
            "servicos": r'id=\"servicos\"',
            "vagas": r'id=\"vagas\"',
            "registro": r'class=\"registration-gateway\"',
            "processo": r'id=\"processo\"',
            "contato": r'id=\"contato\"',
        }
        for name, pattern in selectors.items():
            with self.subTest(section=name):
                self.assertIsNotNone(
                    re.search(pattern, HOME_CONTENT),
                    msg=f"A seção '{name}' deve estar presente na página inicial.",
                )

    def test_navigation_links_include_cadastro(self):
        links = re.findall(r'<a href=\"([^\"]+)\"[^>]*>([^<]+)</a>', HOME_CONTENT)
        cadastro_links = [href for href, text in links if href == "cadastro.html" and "Cadastre" in text]
        perfil_links = [href for href, text in links if href == "perfil.html" and "Atualize" in text]
        self.assertTrue(
            cadastro_links,
            "A navegação deve direcionar usuários para a nova página de cadastro de currículos.",
        )
        self.assertTrue(
            perfil_links,
            "A navegação deve oferecer acesso direto à página de atualização de cadastro.",
        )

    def test_home_header_has_whatsapp_cta(self):
        whatsapp_link = re.search(r'href=\"https://wa\.me/551135391330\"', HOME_CONTENT)
        self.assertIsNotNone(
            whatsapp_link,
            "O cabeçalho da home deve oferecer um botão direto para o canal de WhatsApp informado.",
        )

    def test_home_navigation_targets_existing_sections(self):
        nav_targets = re.findall(r'<a href=\"([^\"]*#[a-zA-Z0-9_-]+)\"', HOME_CONTENT)
        available_ids = set(re.findall(r'id=\"([a-zA-Z0-9_-]+)\"', HOME_CONTENT))
        missing_targets = []
        for target in nav_targets:
            anchor = target.split('#', 1)[1]
            if not anchor:
                continue
            if target.startswith('http'):
                continue
            if anchor not in available_ids:
                missing_targets.append(anchor)
        self.assertFalse(
            missing_targets,
            f"Os links de navegação devem apontar para ids existentes. Alvos faltantes: {missing_targets}",
        )

    def test_jobs_section_has_cards(self):
        cards = re.findall(r'class=\"job-card\"', HOME_CONTENT)
        self.assertGreaterEqual(
            len(cards),
            4,
            "A seção de vagas deve exibir pelo menos quatro cards de oportunidades.",
        )

    def test_job_cards_link_to_cadastro(self):
        apply_links = re.findall(r'<a class=\"btn btn--ghost\" href=\"([^\"]+)\"[^>]*data-action=\"candidatar\"', HOME_CONTENT)
        self.assertTrue(
            all(link == 'cadastro.html' for link in apply_links),
            "Todos os botões de candidatura devem direcionar usuários para a nova página de cadastro.",
        )

    def test_job_cards_have_feedback_placeholder(self):
        feedback_matches = list(
            re.finditer(r'<p class=\"job-card__feedback\"[^>]*data-job-feedback=\"([^"]+)\"[^>]*>', HOME_CONTENT)
        )
        self.assertGreaterEqual(
            len(feedback_matches),
            4,
            "Cada card de vaga precisa oferecer um espaço de mensagem para confirmar a candidatura do usuário.",
        )

        for match in feedback_matches:
            job_id = match.group(1)
            with self.subTest(job=job_id):
                self.assertIn(
                    f'id="{job_id}"',
                    HOME_CONTENT,
                    msg="O feedback de candidatura deve corresponder ao identificador de um card existente.",
                )
                self.assertIn('role="status"', match.group(0))
                self.assertIn('aria-live="polite"', match.group(0))
                self.assertIn('hidden', match.group(0))

    def test_virtual_assistant_chat_widget_present(self):
        self.assertIsNotNone(
            re.search(r'data-assistant-chat', HOME_CONTENT),
            msg="A página inicial deve oferecer um assistente virtual para tirar dúvidas rápidas.",
        )

        self.assertIsNotNone(
            re.search(r'data-assistant-launcher', HOME_CONTENT),
            msg="O assistente precisa ter um botão lançador identificável.",
        )

        quick_actions = re.findall(r'data-assistant-question=\"([a-z-]+)\"', HOME_CONTENT)
        self.assertGreaterEqual(
            len(quick_actions),
            3,
            "O assistente virtual deve conter atalhos com perguntas frequentes para orientar os usuários.",
        )

    def test_assets_exist_and_not_empty(self):
        for asset in (CSS_PATH, MAIN_JS_PATH, LOGIN_JS_PATH, ADMIN_JS_PATH):
            with self.subTest(asset=asset.name):
                self.assertTrue(asset.exists(), f"O arquivo {asset.name} deve existir.")
                self.assertGreater(
                    len(asset.read_text(encoding="utf-8").strip()),
                    0,
                    f"O arquivo {asset.name} não pode estar vazio.",
                )

    def test_admin_panel_requires_login_and_lists_table(self):
        self.assertIsNotNone(
            re.search(r'id=\"admin-login-form\"', ADMIN_CONTENT),
            msg="A página do administrador deve oferecer um formulário de login dedicado.",
        )
        self.assertIsNotNone(
            re.search(r'data-admin-dashboard', ADMIN_CONTENT),
            msg="O painel administrativo deve ter uma área separada para o dashboard.",
        )
        self.assertIsNotNone(
            re.search(r'data-admin-rows', ADMIN_CONTENT),
            msg="A tabela de candidaturas precisa de um corpo identificável para preenchimento dinâmico.",
        )

    def test_talent_form_has_required_fields(self):
        required_fields = {
            "nome": r'id=\"talent-nome\"',
            "email": r'id=\"talent-email\"',
            "senha": r'id=\"talent-senha\"',
            "area": r'id=\"talent-area\"',
            "curriculo": r'id=\"talent-curriculo\"',
        }
        for field, pattern in required_fields.items():
            with self.subTest(field=field):
                self.assertIsNotNone(
                    re.search(pattern, CADASTRO_CONTENT),
                    msg=f"O campo '{field}' deve estar presente no formulário de cadastro de talentos.",
                )

        senha_input = re.search(r'<input[^>]*id=\"talent-senha\"[^>]*>', CADASTRO_CONTENT)
        self.assertIsNotNone(senha_input)
        if senha_input:
            self.assertIn('type="password"', senha_input.group(0))

        file_accept_match = re.search(r'id=\"talent-curriculo\"[^>]+accept=\"([^\"]+)\"', CADASTRO_CONTENT)
        self.assertIsNotNone(file_accept_match, "O upload de currículo deve restringir os formatos permitidos.")
        if file_accept_match:
            accepted_formats = file_accept_match.group(1)
            for expected in [".pdf", ".doc", ".docx"]:
                self.assertIn(
                    expected,
                    accepted_formats,
                    f"O campo de currículo deve aceitar o formato {expected}.",
                )

    def test_profile_section_has_editing_capabilities(self):
        self.assertIsNotNone(
            re.search(r'id=\"perfil\"', PERFIL_CONTENT),
            msg="A página de atualização de cadastro deve expor a área de perfil para edições.",
        )

        profile_fields = {
            "nome": r'id=\"profile-nome\"',
            "email": r'id=\"profile-email\"',
            "area": r'id=\"profile-area\"',
            "curriculo": r'id=\"profile-curriculo\"',
            "senha": r'id=\"profile-senha\"',
        }

        for field, pattern in profile_fields.items():
            with self.subTest(field=field):
                self.assertIsNotNone(
                    re.search(pattern, PERFIL_CONTENT),
                    msg=f"O campo '{field}' deve estar presente no formulário de edição de perfil.",
                )

        password_input = re.search(r'<input[^>]*id=\"profile-senha\"[^>]*>', PERFIL_CONTENT)
        self.assertIsNotNone(password_input)
        if password_input:
            self.assertIn('type="password"', password_input.group(0))

        profile_checkbox = re.search(r'<input[^>]*id=\"profile-alertas\"[^>]*>', PERFIL_CONTENT)
        self.assertIsNotNone(profile_checkbox)
        if profile_checkbox:
            self.assertIn('type="checkbox"', profile_checkbox.group(0))

    def test_secondary_pages_highlight_active_navigation(self):
        self.assertIsNotNone(
            re.search(r'cadastro\.html\"[^>]*aria-current=\"page\"', CADASTRO_CONTENT),
            msg="A página de cadastro deve sinalizar o item ativo no menu.",
        )
        self.assertIsNotNone(
            re.search(r'perfil\.html\"[^>]*aria-current=\"page\"', PERFIL_CONTENT),
            msg="A página de atualização deve manter o estado ativo no menu.",
        )

    def test_login_page_has_auth_tabs_and_forms(self):
        self.assertIsNotNone(
            re.search(r'id=\"login-form\"', LOGIN_CONTENT),
            msg="A página de login deve oferecer um formulário dedicado para candidatos cadastrados.",
        )

        login_password_field = re.search(r'<input[^>]*id=\"login-senha\"[^>]*>', LOGIN_CONTENT)
        self.assertIsNotNone(login_password_field)
        if login_password_field:
            self.assertIn('type="password"', login_password_field.group(0))

        self.assertIsNotNone(
            re.search(r'id=\"register-form\"', LOGIN_CONTENT),
            msg="Usuários sem cadastro precisam encontrar um formulário completo na página de login.",
        )

        register_fields = {
            'register-nome': r'id=\"register-nome\"',
            'register-email': r'id=\"register-email\"',
            'register-senha': r'id=\"register-senha\"',
            'register-area': r'id=\"register-area\"',
            'register-curriculo': r'id=\"register-curriculo\"',
        }

        for field, pattern in register_fields.items():
            with self.subTest(register_field=field):
                self.assertIsNotNone(
                    re.search(pattern, LOGIN_CONTENT),
                    msg=f"O campo '{field}' deve estar disponível no formulário de cadastro da página de login.",
                )

        register_password_field = re.search(r'<input[^>]*id=\"register-senha\"[^>]*>', LOGIN_CONTENT)
        self.assertIsNotNone(register_password_field)
        if register_password_field:
            self.assertIn('type="password"', register_password_field.group(0))

        file_accept_match = re.search(r'id=\"register-curriculo\"[^>]+accept=\"([^\"]+)\"', LOGIN_CONTENT)
        self.assertIsNotNone(
            file_accept_match,
            msg="O cadastro inicial deve restringir os formatos do currículo enviado na tela de login.",
        )
        if file_accept_match:
            accepted_formats = file_accept_match.group(1)
            for expected in [".pdf", ".doc", ".docx"]:
                self.assertIn(
                    expected,
                    accepted_formats,
                    f"O campo de currículo inicial deve aceitar o formato {expected}.",
                )

        for view in ('login', 'register'):
            with self.subTest(toggle=view):
                self.assertIsNotNone(
                    re.search(rf'data-auth-view=\"{view}\"', LOGIN_CONTENT),
                    msg=f"A página de login precisa disponibilizar a aba '{view}' para alternar entre acesso e cadastro.",
                )

    def test_login_page_header_has_whatsapp_cta(self):
        whatsapp_link = re.search(r'href=\"https://wa\.me/551135391330\"', LOGIN_CONTENT)
        self.assertIsNotNone(
            whatsapp_link,
            "O cabeçalho da página de login deve oferecer o botão de WhatsApp atualizado.",
        )

    def test_login_page_uses_dedicated_script(self):
        script_tag = re.search(r'assets/js/login\.js', LOGIN_CONTENT)
        self.assertIsNotNone(
            script_tag,
            "A página de login precisa carregar o script dedicado para autenticação e redirecionamento.",
        )


if __name__ == "__main__":
    unittest.main()
