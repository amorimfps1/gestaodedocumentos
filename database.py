import sqlite3
import os

DB_NAME = 'app.db'


def get_db_path():
    """Retorna o caminho absoluto do banco de dados."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)


def init_db():
    """Inicializa o banco de dados criando as tabelas se não existirem."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Habilitar foreign keys (SQLite não habilita por padrão)
    cursor.execute('PRAGMA foreign_keys = ON')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            tipo TEXT DEFAULT 'geral',
            nome_arquivo TEXT NOT NULL,
            caminho_arquivo TEXT NOT NULL,
            tamanho_bytes INTEGER,
            data_upload DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE
        )
    ''')

    # Índice para acelerar consultas de comentários por documento
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_comentarios_documento
        ON comentarios(documento_id)
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")


if __name__ == '__main__':
    init_db()