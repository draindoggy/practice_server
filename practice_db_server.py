from flask import Flask, jsonify
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

DATABASE_URL = "postgresql://postgres:cCLkjTKUtmcXHuItbeCmfeuZijZxVrEr@nozomi.proxy.rlwy.net:11883/railway"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/data', methods=['GET'])
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username, password FROM users')
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
