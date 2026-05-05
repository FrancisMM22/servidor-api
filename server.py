from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
import google.generativeai as genai  # 🔥 FALTABA ESTO

app = Flask(__name__)

# =========================
# CONFIG GEMINI
# =========================

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")  # 🔥 mejor modelo

# =========================
# DB
# =========================

def conectar():
    db_path = os.path.join(os.getcwd(), "licencias.db")
    return sqlite3.connect(db_path)

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS licencias (
        pc_id TEXT PRIMARY KEY,
        nombre TEXT,
        estado TEXT,
        fecha_inicio TEXT,
        fecha_vencimiento TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ERROR HANDLER
# =========================

@app.errorhandler(Exception)
def handle_error(e):
    print("🔥 ERROR REAL:", e)
    return "Error interno", 500

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "Servidor funcionando 🚀"

# =========================
# VERIFICAR
# =========================

@app.route("/verificar", methods=["GET"])
def verificar():
    pc = request.args.get("pc")

    if not pc:
        return "FALTA PC", 400

    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT estado, fecha_vencimiento FROM licencias WHERE pc_id = ?", (pc,))
    row = c.fetchone()

    if not row:
        inicio = datetime.now()
        vencimiento = inicio + timedelta(days=7)

        c.execute("""
        INSERT INTO licencias (pc_id, nombre, estado, fecha_inicio, fecha_vencimiento)
        VALUES (?, ?, ?, ?, ?)
        """, (
            pc,
            "PRUEBA",
            "ACTIVO",
            inicio.isoformat(),
            vencimiento.isoformat()
        ))

        conn.commit()
        conn.close()
        return "ACTIVO"

    estado, vencimiento = row

    if vencimiento:
        fecha_venc = datetime.fromisoformat(vencimiento)

        if datetime.now() > fecha_venc:
            c.execute("UPDATE licencias SET estado = 'BLOQUEADO' WHERE pc_id = ?", (pc,))
            conn.commit()
            conn.close()
            return "BLOQUEADO"

    conn.close()
    return estado

# =========================
# LISTAR
# =========================

@app.route("/licencias")
def licencias():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT pc_id, nombre, estado, fecha_vencimiento FROM licencias")
    data = c.fetchall()

    conn.close()
    return jsonify(data)

# =========================
# ESTADO
# =========================

@app.route("/estado", methods=["POST"])
def estado():
    data = request.get_json(silent=True)

    if not data:
        return "ERROR: no JSON", 400

    pc = data.get("pc")
    estado = data.get("estado")

    if not pc or not estado:
        return "ERROR: faltan datos", 400

    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE licencias SET estado = ? WHERE pc_id = ?", (estado, pc))
    conn.commit()
    conn.close()

    return "OK"

# =========================
# RENOVAR
# =========================

@app.route("/renovar", methods=["POST"])
def renovar():
    data = request.get_json(silent=True)

    if not data:
        return "ERROR: no JSON", 400

    pc = data.get("pc")

    if not pc:
        return "ERROR: falta pc", 400

    nueva_fecha = datetime.now() + timedelta(days=30)

    conn = conectar()
    c = conn.cursor()

    c.execute("""
    UPDATE licencias 
    SET estado = 'ACTIVO', fecha_vencimiento = ?
    WHERE pc_id = ?
    """, (nueva_fecha.isoformat(), pc))

    conn.commit()
    conn.close()

    return "OK"

# =========================
# CHAT IA
# =========================

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON"}), 400

    mensaje = data.get("mensaje")

    if not mensaje:
        return jsonify({"error": "Falta mensaje"}), 400

    try:
        prompt = f"""
Sos ALBERTO, un asistente virtual argentino, claro, directo y útil.
Respondés de forma natural, amigable y profesional.
No das respuestas genéricas, ayudás de verdad.

Usuario: {mensaje}
"""

        response = model.generate_content(prompt)
        respuesta = response.text

        return jsonify({"respuesta": respuesta})

    except Exception as e:
        print("🔥 ERROR GEMINI:", e)
        return jsonify({"error": "Error con IA"}), 500
# =========================
# PANEL
# =========================

@app.route("/panel")
def panel():
    return "<h2>Panel OK</h2>"

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)