import re
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "index.html"
CSS_PATH = BASE_DIR / "assets" / "css" / "style.css"
JS_PATH = BASE_DIR / "assets" / "js" / "main.js"

HTML_CONTENT = HTML_PATH.read_text(encoding="utf-8")


class TestSiteStructure(unittest.TestCase):
    def test_source_files_without_merge_conflicts(self):
        merge_markers = ("<<<<<<<", "=======", ">>>>>>>")
        tracked_files = [
            HTML_PATH,
            CSS_PATH,
            JS_PATH,
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

    def test_main_sections_present(self):
        selectors = {
            "hero": r'class=\"hero\"',
            "sobre": r'id=\"sobre\"',
            "servicos": r'id=\"servicos\"',
            "vagas": r'id=\"vagas\"',
            "login": r'id=\"login\"',
            "cadastro": r'id=\"cadastro\"',
            "perfil": r'id=\"perfil\"',
            "processo": r'id=\"processo\"',
            "contato": r'id=\"contato\"',
        }
        for name, pattern in selectors.items():
            with self.subTest(section=name):
                self.assertIsNotNone(
                    re.search(pattern, HTML_CONTENT),
                    msg=f"A seção '{name}' deve estar presente na página inicial.",
                )

    def test_navigation_links_include_cadastro(self):
        links = re.findall(r'<a href=\"(#.*?)\"[^>]*>([^<]+)</a>', HTML_CONTENT)
        cadastro_links = [href for href, text in links if href == "#cadastro" and "Cadastre" in text]
        self.assertTrue(
            cadastro_links,
            "O menu principal deve manter um link direto para a seção de cadastro de talentos.",
        )

    def test_navigation_links_include_login(self):
        links = re.findall(r'<a href=\"(#.*?)\"[^>]*>([^<]+)</a>', HTML_CONTENT)
        login_links = [href for href, text in links if href == "#login" and "Login" in text]
        self.assertTrue(
            login_links,
            "O menu principal deve oferecer um acesso direto à área de login dos candidatos.",
        )

    def test_navigation_targets_existing_sections(self):
        nav_targets = re.findall(r'<a href="(#[a-z-]+)"', HTML_CONTENT)
        available_ids = set(re.findall(r'id=\"([a-z-]+)\"', HTML_CONTENT))
        missing_targets = [target for target in nav_targets if target.startswith('#') and target[1:] not in available_ids]
        self.assertFalse(
            missing_targets,
            f"Os links de navegação devem apontar para ids existentes. Alvos faltantes: {missing_targets}",
        )

    def test_jobs_section_has_cards(self):
        cards = re.findall(r'class=\"job-card\"', HTML_CONTENT)
        self.assertGreaterEqual(
            len(cards),
            4,
            "A seção de vagas deve exibir pelo menos quatro cards de oportunidades.",
        )

    def test_assets_exist_and_not_empty(self):
        self.assertTrue(CSS_PATH.exists(), "O arquivo de estilos deve existir.")
        self.assertGreater(
            len(CSS_PATH.read_text(encoding="utf-8").strip()),
            0,
            "O arquivo de estilos não pode estar vazio.",
        )
        self.assertTrue(JS_PATH.exists(), "O arquivo de scripts deve existir.")
        self.assertGreater(
            len(JS_PATH.read_text(encoding="utf-8").strip()),
            0,
            "O arquivo de scripts não pode estar vazio.",
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
                    re.search(pattern, HTML_CONTENT),
                    msg=f"O campo '{field}' deve estar presente no formulário de cadastro de talentos.",
                )

        senha_input = re.search(r'<input[^>]*id=\"talent-senha\"[^>]*>', HTML_CONTENT)
        self.assertIsNotNone(senha_input)
        if senha_input:
            self.assertIn('type="password"', senha_input.group(0))

        file_accept_match = re.search(r'id=\"talent-curriculo\"[^>]+accept=\"([^\"]+)\"', HTML_CONTENT)
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
            re.search(r'id=\"perfil\"', HTML_CONTENT),
            msg="A área de perfil deve estar presente para permitir atualizações de cadastro.",
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
                    re.search(pattern, HTML_CONTENT),
                    msg=f"O campo '{field}' deve estar presente no formulário de edição de perfil.",
                )

        profile_password_input = re.search(r'<input[^>]*id=\"profile-senha\"[^>]*>', HTML_CONTENT)
        self.assertIsNotNone(profile_password_input)
        if profile_password_input:
            self.assertIn('type="password"', profile_password_input.group(0))

        profile_checkbox = re.search(r'<input[^>]*id=\"profile-alertas\"[^>]*>', HTML_CONTENT)
        self.assertIsNotNone(
            profile_checkbox,
            "O formulário de perfil deve permitir ativar ou desativar alertas por e-mail.",
        )
        if profile_checkbox:
            self.assertIn(
                'type="checkbox"',
                profile_checkbox.group(0),
                "O campo de alertas deve ser um checkbox para controlar as notificações.",
            )

    def test_login_section_has_form_and_recommendations(self):
        self.assertIsNotNone(
            re.search(r'id=\"login-form\"', HTML_CONTENT),
            msg="A página deve oferecer um formulário de login dedicado para candidatos cadastrados.",
        )

        self.assertIsNotNone(
            re.search(r'class=\"login__recommendations\"', HTML_CONTENT),
            msg="A seção de login deve expor um bloco para recomendações personalizadas.",
        )

        login_password_field = re.search(r'<input[^>]*id=\"login-senha\"[^>]*>', HTML_CONTENT)
        self.assertIsNotNone(login_password_field)
        if login_password_field:
            self.assertIn('type="password"', login_password_field.group(0))

    def test_job_cards_redirect_candidates_to_login(self):
        apply_links = re.findall(r'<a class=\"btn btn--ghost\" href=\"(#[a-z-]+)\"[^>]*data-action=\"candidatar\"', HTML_CONTENT)
        self.assertTrue(
            all(link == '#login' for link in apply_links),
            "Todos os botões de candidatura devem direcionar usuários para a área de login.",
        )


if __name__ == "__main__":
    unittest.main()
