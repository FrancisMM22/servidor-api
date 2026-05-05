from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
import google.generativeai as genai  # 🔥 FALTABA ESTO

app = Flask(__name__)

# =========================
# CONFIG GEMINI
# =========================
gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("Default_Gemini_API_Key")

if not gemini_key:
    print("🔥 ERROR: No se encontró ninguna API KEY en las variables de entorno")

genai.configure(api_key=gemini_key)

# Usamos el nombre estándar que aceptan las versiones nuevas
model = genai.GenerativeModel("gemini-1.5-flash")
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
        # Prompt mejorado para que mantenga la personalidad
        prompt = f"Sos ALBERTO, un asistente virtual argentino, amigable y directo. Usuario: {mensaje}"

        response = model.generate_content(prompt)
        
        # Verificamos si la respuesta tiene contenido válido
        if response.candidates and len(response.candidates[0].content.parts) > 0:
            respuesta = response.text
        else:
            respuesta = "Che, no te pude entender bien. ¿Me repetís?"

        return jsonify({"respuesta": respuesta})

    except Exception as e:
        # Esto te va a mostrar el error exacto en los logs de Render
        print(f"🔥 ERROR GEMINI DETALLADO: {str(e)}")
        return jsonify({"error": "Error con la IA", "detalles": str(e)}), 500
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
    # Render asigna el puerto en la variable PORT
    puerto = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=puerto)