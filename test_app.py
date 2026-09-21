import unittest
import os
import io
import json
import tempfile
import sqlite3

# Configurar ambiente de teste antes de importar o app
os.environ['FLASK_DEBUG'] = 'false'

from app import app, get_db_connection
from database import init_db


class SistemaDocumentalTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Cria pasta temporária para uploads durante os testes
        self.test_upload_dir = tempfile.mkdtemp()
        app.config['UPLOAD_FOLDER'] = self.test_upload_dir

        # Cria banco de dados temporário isolado para os testes
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        os.environ['DATABASE_PATH'] = self.temp_db.name
        init_db()

    def tearDown(self):
        # Limpar arquivos da pasta temporária
        for f in os.listdir(self.test_upload_dir):
            caminho = os.path.join(self.test_upload_dir, f)
            if os.path.isfile(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass
        try:
            os.rmdir(self.test_upload_dir)
        except OSError:
            pass

        # Remover banco temporário
        if os.environ.get('DATABASE_PATH') == self.temp_db.name:
            del os.environ['DATABASE_PATH']
        if os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except OSError:
                pass

    def test_frontend_renders_filter_sections(self):
        """Verifica se a interface web principal renderiza os filtros de formato e tipo."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('Formato:', html)
        self.assertIn('Tipo:', html)
        self.assertIn('pills-ext', html)
        self.assertIn('pills-tipo', html)
        self.assertIn('btn-reset-filters', html)
        self.assertIn('setExtFilter', html)
        self.assertIn('setTypeFilter', html)

    def test_upload_com_tipo_e_persistencia(self):
        """Testa o upload de documento especificando o tipo (ex: contrato)."""
        dados = {
            'titulo': 'Contrato de Parceria Comercial',
            'descricao': 'Contrato firmado entre empresas parceiras',
            'tipo': 'contrato',
            'arquivo': (io.BytesIO(b'%PDF-1.4 test content'), 'contrato_parceria.pdf')
        }
        res = self.client.post('/api/documentos', data=dados, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 201)
        resp_json = res.get_json()
        self.assertIn('id', resp_json)
        doc_id = resp_json['id']

        # Verifica persistência no banco
        res_detalhe = self.client.get(f'/api/documentos/{doc_id}')
        self.assertEqual(res_detalhe.status_code, 200)
        doc = res_detalhe.get_json()
        self.assertEqual(doc['titulo'], 'Contrato de Parceria Comercial')
        self.assertEqual(doc['tipo'], 'contrato')

    def test_filtros_api_por_tipo_e_extensao(self):
        """Testa listagem e filtragem por tipo e extensão via API REST."""
        # 1. Upload de contrato PDF
        self.client.post('/api/documentos', data={
            'titulo': 'Contrato Alpha',
            'descricao': 'Contrato em PDF',
            'tipo': 'contrato',
            'arquivo': (io.BytesIO(b'%PDF-1.4 sample'), 'contrato_alpha.pdf')
        }, content_type='multipart/form-data')

        # 2. Upload de petição PDF
        self.client.post('/api/documentos', data={
            'titulo': 'Petição Inicial',
            'descricao': 'Petição em PDF',
            'tipo': 'petição',
            'arquivo': (io.BytesIO(b'%PDF-1.4 sample'), 'peticao_inicial.pdf')
        }, content_type='multipart/form-data')

        # 3. Upload de contrato JPG
        self.client.post('/api/documentos', data={
            'titulo': 'Contrato Escaneado',
            'descricao': 'Contrato em imagem JPG',
            'tipo': 'contrato',
            'arquivo': (io.BytesIO(b'\xff\xd8\xff sample'), 'contrato_scan.jpg')
        }, content_type='multipart/form-data')

        # 4. Upload de documento geral PNG
        self.client.post('/api/documentos', data={
            'titulo': 'Comprovante Geral',
            'descricao': 'Comprovante em imagem PNG',
            'tipo': 'geral',
            'arquivo': (io.BytesIO(b'\x89PNG sample'), 'comprovante.png')
        }, content_type='multipart/form-data')

        # Consulta todos os documentos (deve retornar 4)
        res_todos = self.client.get('/api/documentos')
        self.assertEqual(res_todos.status_code, 200)
        docs_todos = res_todos.get_json()
        self.assertEqual(len(docs_todos), 4)

        # Filtro por tipo=contrato (deve retornar 2: contrato_alpha.pdf e contrato_scan.jpg)
        res_contratos = self.client.get('/api/documentos?tipo=contrato')
        self.assertEqual(res_contratos.status_code, 200)
        contratos = res_contratos.get_json()
        self.assertEqual(len(contratos), 2)
        for c in contratos:
            self.assertEqual(c['tipo'], 'contrato')

        # Filtro por tipo=petição (deve retornar 1: peticao_inicial.pdf)
        res_peticao = self.client.get('/api/documentos?tipo=petição')
        self.assertEqual(res_peticao.status_code, 200)
        peticoes = res_peticao.get_json()
        self.assertEqual(len(peticoes), 1)
        self.assertEqual(peticoes[0]['titulo'], 'Petição Inicial')

        # Filtro por ext=pdf (deve retornar 2: contrato_alpha.pdf e peticao_inicial.pdf)
        res_pdf = self.client.get('/api/documentos?ext=pdf')
        self.assertEqual(res_pdf.status_code, 200)
        pdfs = res_pdf.get_json()
        self.assertEqual(len(pdfs), 2)

        # Filtro combinado: tipo=contrato E ext=pdf (deve retornar 1: contrato_alpha.pdf)
        res_contrato_pdf = self.client.get('/api/documentos?tipo=contrato&ext=pdf')
        self.assertEqual(res_contrato_pdf.status_code, 200)
        contratos_pdf = res_contrato_pdf.get_json()
        self.assertEqual(len(contratos_pdf), 1)
        self.assertEqual(contratos_pdf[0]['titulo'], 'Contrato Alpha')

    def test_comentarios_e_delecao(self):
        """Testa adição de comentários e deleção de documento."""
        res_upload = self.client.post('/api/documentos', data={
            'titulo': 'Certidão de Nascimento',
            'tipo': 'certidão',
            'arquivo': (io.BytesIO(b'%PDF-1.4 certidao'), 'certidao.pdf')
        }, content_type='multipart/form-data')
        doc_id = res_upload.get_json()['id']

        # Adicionar comentário
        res_com = self.client.post(f'/api/documentos/{doc_id}/comentarios', json={'texto': 'Documento validado'})
        self.assertEqual(res_com.status_code, 201)

        # Listar comentários
        res_list_com = self.client.get(f'/api/documentos/{doc_id}/comentarios')
        self.assertEqual(res_list_com.status_code, 200)
        comentarios = res_list_com.get_json()
        self.assertEqual(len(comentarios), 1)
        self.assertEqual(comentarios[0]['texto'], 'Documento validado')

        # Deletar documento
        res_del = self.client.delete(f'/api/documentos/{doc_id}')
        self.assertEqual(res_del.status_code, 200)

        # Confirmar que não existe mais
        res_check = self.client.get(f'/api/documentos/{doc_id}')
        self.assertEqual(res_check.status_code, 404)

    def test_swagger_schema_and_docs_endpoint(self):
        """Verifica se o Swagger UI e o schema OpenAPI contêm todas as rotas, modelos e parâmetros atualizados."""
        # 1. Endpoint /docs
        res_docs = self.client.get('/docs', follow_redirects=True)
        self.assertEqual(res_docs.status_code, 200)

        # 2. Schema /swagger.json
        res_swagger = self.client.get('/swagger.json')
        self.assertEqual(res_swagger.status_code, 200)
        swagger = res_swagger.get_json()

        # Parâmetros de GET /api/documentos
        get_params = {p['name']: p for p in swagger['paths']['/api/documentos']['get'].get('parameters', [])}
        self.assertIn('tipo', get_params)
        self.assertEqual(get_params['tipo']['in'], 'query')
        self.assertIn('ext', get_params)
        self.assertEqual(get_params['ext']['in'], 'query')

        # Parâmetros de POST /api/documentos (multipart/form-data)
        post_params = {p['name']: p for p in swagger['paths']['/api/documentos']['post'].get('parameters', [])}
        self.assertIn('arquivo', post_params)
        self.assertIn('titulo', post_params)
        self.assertIn('descricao', post_params)
        self.assertIn('tipo', post_params)
        self.assertEqual(post_params['tipo']['in'], 'formData')

        # Modelos
        definitions = swagger.get('definitions', {})
        self.assertIn('Documento', definitions)
        self.assertIn('tipo', definitions['Documento']['properties'])
        self.assertIn('Comentario', definitions)
        self.assertIn('ComentarioInput', definitions)

    def test_filtros_com_acentos_e_caixa_alta(self):
        """Verifica suporte a case insensitivity na API."""
        self.client.post('/api/documentos', data={
            'titulo': 'Contrato Caixa Alta',
            'tipo': 'contrato',
            'arquivo': (io.BytesIO(b'%PDF-1.4 c'), 'doc1.pdf')
        }, content_type='multipart/form-data')

        self.client.post('/api/documentos', data={
            'titulo': 'Petição com Acento',
            'tipo': 'petição',
            'arquivo': (io.BytesIO(b'%PDF-1.4 p'), 'doc2.pdf')
        }, content_type='multipart/form-data')

        # Teste com maiúsculas
        r_tipo_upper = self.client.get('/api/documentos?tipo=CONTRATO')
        self.assertEqual(r_tipo_upper.status_code, 200)
        self.assertEqual(len(r_tipo_upper.get_json()), 1)

        r_ext_upper = self.client.get('/api/documentos?ext=PDF')
        self.assertEqual(r_ext_upper.status_code, 200)
        self.assertEqual(len(r_ext_upper.get_json()), 2)


if __name__ == '__main__':
    unittest.main()

