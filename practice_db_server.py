from flask import Flask, jsonify
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host='127.0.0.1',
        database='os_db',
        user='postgres',
        password=111,
        port=5433
    )
    return conn

@app.route('/data', methods=['GET'])
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username, secret_phraze FROM users')
    rows = cur.fetchall()

    colnames = [desc[0] for desc in cur.description]

    result = []
    for row in rows:
        result.append(dict(zip(colnames, row)))

    cur.close()
    conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
