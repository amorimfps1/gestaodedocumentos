from flask import Flask, Blueprint, request, jsonify, render_template, send_from_directory
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from contextlib import contextmanager
import sqlite3
import os
import uuid

from database import init_db, get_db_path

app = Flask(__name__)

# --- Configurações ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB máximo

# Criar pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# --- Utilitários ---

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida."""
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@contextmanager
def get_db_connection():
    """Context manager para conexão com o banco de dados.
    Garante que a conexão é sempre fechada, mesmo em caso de erro."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
    finally:
        conn.close()


# --- Rotas Frontend e Uploads (Flask puro) ---

@app.route('/')
def index():
    """Interface web principal do sistema."""
    return render_template('index.html')


@app.route('/uploads/<nome_arquivo>')
def visualizar_arquivo(nome_arquivo):
    """Serve o arquivo para visualização ou download."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], nome_arquivo)


# --- Blueprint e Configuração do Swagger (Flask-RESTX) ---

api_bp = Blueprint('api_bp', __name__)

api = Api(
    api_bp,
    version='1.0',
    title='Sistema de Gestão Documental - API',
    description='API REST para gerenciamento de documentos e comentários com documentação interativa Swagger.',
    doc='/docs'
)

ns = api.namespace('api/documentos', description='Operações com documentos e comentários')

# Modelos para documentação Swagger
documento_model = api.model('Documento', {
    'id': fields.Integer(readOnly=True, description='Identificador único do documento', example=1),
    'titulo': fields.String(required=True, description='Título do documento', example='Contrato de Prestação de Serviços'),
    'descricao': fields.String(description='Descrição detalhada do documento', example='Contrato firmado com cliente X'),
    'tipo': fields.String(description='Tipo/categoria do documento', example='geral'),
    'nome_arquivo': fields.String(readOnly=True, description='Nome do arquivo salvo no disco', example='abc123_contrato.pdf'),
    'tamanho_bytes': fields.Integer(readOnly=True, description='Tamanho do arquivo em bytes', example=1048576),
    'data_upload': fields.String(readOnly=True, description='Data e hora do envio', example='2026-09-20 15:00:00')
})

comentario_input = api.model('ComentarioInput', {
    'texto': fields.String(required=True, description='Texto do comentário', example='Documento revisado e aprovado.')
})

comentario_model = api.model('Comentario', {
    'id': fields.Integer(readOnly=True, description='Identificador único do comentário', example=1),
    'documento_id': fields.Integer(readOnly=True, description='ID do documento associado', example=1),
    'texto': fields.String(description='Texto do comentário', example='Documento revisado e aprovado.'),
    'data_registro': fields.String(description='Data e hora do registro', example='2026-09-20 15:30:00')
})

mensagem_model = api.model('MensagemSucesso', {
    'mensagem': fields.String(description='Mensagem de sucesso', example='Operação realizada com sucesso')
})

erro_model = api.model('MensagemErro', {
    'erro': fields.String(description='Descrição do erro', example='Recurso não encontrado')
})

# Parser para upload multipart/form-data no Swagger
upload_parser = api.parser()
upload_parser.add_argument('arquivo', location='files', type=FileStorage, required=True, help='Arquivo (PDF, JPG, PNG - máx. 16 MB)')
upload_parser.add_argument('titulo', location='form', type=str, required=True, help='Título do documento')
upload_parser.add_argument('descricao', location='form', type=str, required=False, help='Descrição do documento')
upload_parser.add_argument('tipo', location='form', type=str, required=False, default='geral', help='Tipo/categoria do documento (ex: geral, contrato, procuração, petição, certidão, outro)')


# --- Endpoints da API ---

@ns.route('')
class DocumentoLista(Resource):
    @ns.doc('listar_documentos', params={
        'tipo': 'Filtrar documentos por tipo (ex: geral, contrato, procuração, petição, certidão, outro)',
        'ext': 'Filtrar documentos por extensão (ex: pdf, jpg, png)'
    })
    @ns.marshal_list_with(documento_model)
    @ns.response(200, 'Lista de documentos retornada com sucesso')
    def get(self):
        """Lista os documentos cadastrados, com suporte a filtros opcionais por tipo e extensão."""
        tipo_filtro = request.args.get('tipo', '').strip().lower()
        ext_filtro = request.args.get('ext', '').strip().lower()

        query = 'SELECT id, titulo, descricao, tipo, nome_arquivo, tamanho_bytes, data_upload FROM documentos WHERE 1=1'
        params = []

        if tipo_filtro and tipo_filtro != 'todos':
            query += ' AND lower(tipo) = ?'
            params.append(tipo_filtro)

        if ext_filtro and ext_filtro != 'todos':
            query += ' AND lower(nome_arquivo) LIKE ?'
            params.append(f'%.{ext_filtro}')

        query += ' ORDER BY data_upload DESC'

        with get_db_connection() as conn:
            documentos = conn.execute(query, params).fetchall()
        return [dict(doc) for doc in documentos], 200

    @ns.doc('upload_documento')
    @ns.expect(upload_parser)
    @ns.response(201, 'Documento salvo com sucesso', mensagem_model)
    @ns.response(400, 'Dados inválidos ou arquivo não permitido', erro_model)
    def post(self):
        """Faz upload de um novo documento."""
        if 'arquivo' not in request.files:
            return {'erro': 'Nenhum arquivo enviado'}, 400

        arquivo = request.files['arquivo']
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao', '')
        tipo = request.form.get('tipo', 'geral')
        if not tipo or not tipo.strip():
            tipo = 'geral'
        else:
            tipo = tipo.strip().lower()

        if not arquivo or arquivo.filename == '' or not titulo or not titulo.strip():
            return {'erro': 'Arquivo e título são obrigatórios'}, 400

        titulo = titulo.strip()
        descricao = descricao.strip() if descricao else ''

        if not allowed_file(arquivo.filename):
            return {'erro': 'Formato de arquivo não permitido (apenas PDF, JPG, PNG)'}, 400

        # Gerar nome único para evitar sobreescrita
        filename = secure_filename(arquivo.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        caminho_salvamento = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        arquivo.save(caminho_salvamento)

        tamanho = os.path.getsize(caminho_salvamento)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO documentos (titulo, descricao, tipo, nome_arquivo, caminho_arquivo, tamanho_bytes) VALUES (?, ?, ?, ?, ?, ?)',
                    (titulo, descricao, tipo, unique_name, caminho_salvamento, tamanho)
                )
                conn.commit()
                novo_id = cursor.lastrowid
        except Exception:
            if os.path.exists(caminho_salvamento):
                try:
                    os.remove(caminho_salvamento)
                except OSError:
                    pass
            raise

        return {'mensagem': 'Documento salvo com sucesso', 'id': novo_id}, 201


@ns.route('/<int:doc_id>')
@ns.param('doc_id', 'Identificador do documento')
class DocumentoDetalhe(Resource):
    @ns.doc('obter_documento')
    @ns.response(200, 'Detalhes do documento', documento_model)
    @ns.response(404, 'Documento não encontrado', erro_model)
    def get(self, doc_id):
        """Obtém detalhes de um documento específico."""
        with get_db_connection() as conn:
            documento = conn.execute(
                'SELECT id, titulo, descricao, tipo, nome_arquivo, tamanho_bytes, data_upload FROM documentos WHERE id = ?',
                (doc_id,)
            ).fetchone()

        if documento is None:
            return {'erro': 'Documento não encontrado'}, 404

        return dict(documento), 200

    @ns.doc('deletar_documento')
    @ns.response(200, 'Documento deletado com sucesso', mensagem_model)
    @ns.response(404, 'Documento não encontrado', erro_model)
    def delete(self, doc_id):
        """Deleta um documento e seus comentários associados."""
        with get_db_connection() as conn:
            documento = conn.execute(
                'SELECT caminho_arquivo FROM documentos WHERE id = ?', (doc_id,)
            ).fetchone()

            if documento is None:
                return {'erro': 'Documento não encontrado'}, 404

            if os.path.exists(documento['caminho_arquivo']):
                os.remove(documento['caminho_arquivo'])

            conn.execute('DELETE FROM documentos WHERE id = ?', (doc_id,))
            conn.commit()

        return {'mensagem': 'Documento deletado com sucesso'}, 200


@ns.route('/<int:doc_id>/comentarios')
@ns.param('doc_id', 'Identificador do documento')
class ComentarioLista(Resource):
    @ns.doc('listar_comentarios')
    @ns.response(200, 'Lista de comentários do documento', [comentario_model])
    @ns.response(404, 'Documento não encontrado', erro_model)
    def get(self, doc_id):
        """Lista os comentários de um documento."""
        with get_db_connection() as conn:
            doc = conn.execute('SELECT id FROM documentos WHERE id = ?', (doc_id,)).fetchone()
            if doc is None:
                return {'erro': 'Documento não encontrado'}, 404

            comentarios = conn.execute(
                'SELECT id, documento_id, texto, data_registro FROM comentarios WHERE documento_id = ? ORDER BY data_registro DESC',
                (doc_id,)
            ).fetchall()

        return [dict(com) for com in comentarios], 200

    @ns.doc('adicionar_comentario')
    @ns.expect(comentario_input)
    @ns.response(201, 'Comentário adicionado com sucesso', mensagem_model)
    @ns.response(400, 'Texto do comentário é obrigatório', erro_model)
    @ns.response(404, 'Documento não encontrado', erro_model)
    def post(self, doc_id):
        """Adiciona um comentário a um documento."""
        with get_db_connection() as conn:
            doc = conn.execute('SELECT id FROM documentos WHERE id = ?', (doc_id,)).fetchone()
            if doc is None:
                return {'erro': 'Documento não encontrado'}, 404

            dados = request.get_json(silent=True)
            if not dados or not dados.get('texto') or not dados.get('texto').strip():
                return {'erro': 'O texto do comentário é obrigatório'}, 400

            texto = dados['texto'].strip()
            conn.execute(
                'INSERT INTO comentarios (documento_id, texto) VALUES (?, ?)',
                (doc_id, texto)
            )
            conn.commit()

        return {'mensagem': 'Comentário adicionado!'}, 201


# Registrar o Blueprint da API no App
app.register_blueprint(api_bp)

# --- Inicialização ---

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)