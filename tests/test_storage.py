import os
import tempfile
import unittest
from pathlib import Path

import storage


class StorageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ['IDEAL_DATA_DIR'] = self.tmpdir.name
        storage.initialize_database()

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop('IDEAL_DATA_DIR', None)

    def test_save_candidate_persists_record_and_file(self):
        payload = {
            'nome': 'Maria da Silva',
            'email': 'maria@example.com',
            'telefone': '(11) 99999-9999',
            'area': 'tecnologia',
            'deseja_alertas': True,
        }

        candidate = storage.save_candidate(
            payload,
            resume_filename='curriculo.pdf',
            resume_data=b'conteudo do curriculo',
        )

        data_dir = Path(self.tmpdir.name)
        db_path = data_dir / 'site.db'
        self.assertTrue(db_path.exists(), 'O banco de dados deve ser criado automaticamente.')

        uploads_dir = data_dir / 'uploads'
        self.assertTrue(uploads_dir.exists(), 'A pasta de uploads deve ser criada automaticamente.')

        self.assertTrue(candidate['curriculo'].startswith('uploads/'))
        uploaded_file = data_dir / candidate['curriculo']
        self.assertTrue(uploaded_file.exists(), 'O currículo enviado deve ser armazenado na pasta de uploads.')

        stored = storage.get_candidate_by_email('maria@example.com')
        self.assertIsNotNone(stored)
        self.assertEqual(stored['email'], 'maria@example.com')
        self.assertEqual(stored['area'], 'tecnologia')
        self.assertTrue(stored['desejaAlertas'])

    def test_update_candidate_without_new_file_keeps_existing_resume(self):
        payload = {
            'nome': 'João Pereira',
            'email': 'joao@example.com',
            'telefone': '(11) 98888-8888',
            'area': 'marketing',
            'deseja_alertas': True,
        }

        first = storage.save_candidate(
            payload,
            resume_filename='joao.docx',
            resume_data=b'curriculo inicial',
        )

        updated_payload = {
            'nome': 'João Pereira',
            'email': 'joao@example.com',
            'telefone': '(11) 97777-7777',
            'area': 'financeiro',
            'deseja_alertas': False,
        }

        second = storage.save_candidate(updated_payload)

        self.assertEqual(first['curriculo'], second['curriculo'], 'Sem novo arquivo o currículo deve ser mantido.')
        stored = storage.get_candidate_by_email('joao@example.com')
        self.assertEqual(stored['area'], 'financeiro')
        self.assertFalse(stored['desejaAlertas'])

        data_dir = Path(self.tmpdir.name)
        uploaded_file = data_dir / second['curriculo']
        self.assertTrue(uploaded_file.exists(), 'O currículo original deve continuar disponível após a atualização.')


if __name__ == '__main__':
    unittest.main()
