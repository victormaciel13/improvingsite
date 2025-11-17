import os
import tempfile
import unittest
from pathlib import Path

import sqlite3

import storage


class StorageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ['IDEAL_DATA_DIR'] = self.tmpdir.name
        storage.initialize_database()

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop('IDEAL_DATA_DIR', None)

    def test_create_or_update_candidate_persists_record_and_file(self):
        payload = {
            'nome': 'Maria da Silva',
            'email': 'maria@example.com',
            'telefone': '(11) 99999-9999',
            'area_interesse': 'tecnologia',
            'recebe_alertas': True,
            'senha': 'segura123',
        }

        candidate = storage.create_or_update_candidate(
            payload,
            resume_filename='curriculo.pdf',
            resume_data=b'conteudo do curriculo',
        )

        data_dir = Path(self.tmpdir.name)
        db_path = data_dir / 'site.db'
        self.assertTrue(db_path.exists(), 'O banco de dados deve ser criado automaticamente.')

        uploads_dir = data_dir / 'uploads'
        self.assertTrue(uploads_dir.exists(), 'A pasta de uploads deve ser criada automaticamente.')

        self.assertTrue(candidate['curriculoPath'].startswith('uploads/'))
        uploaded_file = data_dir / candidate['curriculoPath']
        self.assertTrue(uploaded_file.exists(), 'O currículo enviado deve ser armazenado na pasta de uploads.')

        stored = storage.get_candidate_by_email('maria@example.com')
        self.assertIsNotNone(stored)
        self.assertEqual(stored['email'], 'maria@example.com')
        self.assertEqual(stored['areaInteresse'], 'tecnologia')
        self.assertTrue(stored['recebeAlertas'])
        authenticated = storage.validate_login('maria@example.com', 'segura123')
        self.assertEqual(authenticated['email'], 'maria@example.com')

        with sqlite3.connect(data_dir / 'site.db') as conn:
            row = conn.execute('SELECT senha_hash FROM candidates WHERE email = ?', ('maria@example.com',)).fetchone()
        self.assertIsNotNone(row)
        self.assertNotIn('segura123', row[0], 'A senha não deve ser armazenada em texto puro.')

    def test_update_candidate_without_new_file_keeps_existing_resume(self):
        payload = {
            'nome': 'João Pereira',
            'email': 'joao@example.com',
            'telefone': '(11) 98888-8888',
            'area_interesse': 'marketing',
            'recebe_alertas': True,
            'senha': 'senhaInicial1',
        }

        first = storage.create_or_update_candidate(
            payload,
            resume_filename='joao.docx',
            resume_data=b'curriculo inicial',
        )

        updated_payload = {
            'nome': 'João Pereira',
            'email': 'joao@example.com',
            'telefone': '(11) 97777-7777',
            'area_interesse': 'financeiro',
            'recebe_alertas': False,
            'senha': 'NovaSenha2',
        }

        second = storage.create_or_update_candidate(updated_payload)

        self.assertEqual(first['curriculoPath'], second['curriculoPath'], 'Sem novo arquivo o currículo deve ser mantido.')
        stored = storage.get_candidate_by_email('joao@example.com')
        self.assertEqual(stored['areaInteresse'], 'financeiro')
        self.assertFalse(stored['recebeAlertas'])
        updated_auth = storage.validate_login('joao@example.com', 'NovaSenha2')
        self.assertEqual(updated_auth['email'], 'joao@example.com')
        with self.assertRaises(storage.AuthenticationError):
            storage.validate_login('joao@example.com', 'senhaInicial1')

        data_dir = Path(self.tmpdir.name)
        uploaded_file = data_dir / second['curriculoPath']
        self.assertTrue(uploaded_file.exists(), 'O currículo original deve continuar disponível após a atualização.')

    def test_validate_login_with_invalid_credentials(self):
        payload = {
            'nome': 'Ana Souza',
            'email': 'ana@example.com',
            'telefone': '(11) 95555-5555',
            'area_interesse': 'tecnologia',
            'recebe_alertas': True,
            'senha': 'SenhaForte3',
        }

        storage.create_or_update_candidate(payload)

        with self.assertRaises(storage.AuthenticationError):
            storage.validate_login('ana@example.com', 'senhaIncorreta')


if __name__ == '__main__':
    unittest.main()
