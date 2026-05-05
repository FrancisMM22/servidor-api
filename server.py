from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

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

# 🔥 IMPORTANTE: esto corre SIEMPRE (también en Render)
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
# AUTO REGISTRO + VERIFICAR
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

    # 🆕 SI NO EXISTE → CREAR PRUEBA
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

    # ⏳ CONTROL DE VENCIMIENTO
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
# LISTAR PCs
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
# CAMBIAR ESTADO
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
# PANEL
# =========================

@app.route("/panel")
def panel():
    return """
    <html>
    <body style="font-family: Arial; background:#f4f6f8; text-align:center;">
        <h2>Panel de Licencias</h2>

        <button onclick="cargar()">Actualizar</button>
        <br><br>

        <table border="1" style="margin:auto; background:white;">
            <thead>
                <tr>
                    <th>PC ID</th>
                    <th>Estado</th>
                    <th>Días restantes</th>
                    <th>Acción</th>
                </tr>
            </thead>
            <tbody id="tabla"></tbody>
        </table>

        <script>
            function cargar(){
                fetch('/licencias')
                .then(res => res.json())
                .then(data => {
                    let html = "";

                    data.forEach(row => {
                        let venc = row[3];
                        let dias = "-";

                        if (venc){
                            let fecha = new Date(venc);
                            let hoy = new Date();
                            let diff = Math.ceil((fecha - hoy) / (1000 * 60 * 60 * 24));
                            dias = diff + " días";
                        }

                        html += `
                        <tr>
                            <td>${row[0]}</td>
                            <td>${row[2]}</td>
                            <td>${dias}</td>
                            <td>
                                <button onclick="activar('${row[0]}')">Activar</button>
                                <button onclick="bloquear('${row[0]}')">Bloquear</button>
                                <button onclick="renovar('${row[0]}')">Renovar</button>
                            </td>
                        </tr>`;
                    });

                    document.getElementById("tabla").innerHTML = html;
                });
            }

            function activar(pc){
                fetch('/estado', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({pc: pc, estado:'ACTIVO'})
                }).then(()=>cargar());
            }

            function bloquear(pc){
                fetch('/estado', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({pc: pc, estado:'BLOQUEADO'})
                }).then(()=>cargar());
            }

            function renovar(pc){
                fetch('/renovar', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({pc: pc})
                }).then(()=>cargar());
            }

            cargar();
        </script>
    </body>
    </html>
    """

# =========================
# RUN LOCAL
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)