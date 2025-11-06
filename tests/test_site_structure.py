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
            "cadastro": r'id=\"cadastro\"',
            "processo": r'id=\"processo\"',
            "contato": r'id=\"contato\"',
        }
        for name, pattern in selectors.items():
            with self.subTest(section=name):
                self.assertIsNotNone(
                    re.search(pattern, HTML_CONTENT),
                    msg=f"A seção '{name}' deve estar presente na página inicial.",
                )

    def test_whatsapp_cta_link(self):
        match = re.search(r'href=\"(https://wa\.me/[^\"]+)\"', HTML_CONTENT)
        self.assertIsNotNone(match, "Deve existir um link para contato via WhatsApp.")
        if match:
            self.assertTrue(
                match.group(1).startswith("https://wa.me/"),
                "O link do WhatsApp deve utilizar o domínio oficial wa.me.",
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
            "area": r'id=\"talent-area\"',
            "curriculo": r'id=\"talent-curriculo\"',
        }
        for field, pattern in required_fields.items():
            with self.subTest(field=field):
                self.assertIsNotNone(
                    re.search(pattern, HTML_CONTENT),
                    msg=f"O campo '{field}' deve estar presente no formulário de cadastro de talentos.",
                )

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


if __name__ == "__main__":
    unittest.main()
