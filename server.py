from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# =========================
# DB
# =========================
def conectar():
    return sqlite3.connect("licencias.db")

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS licencias (
        usuario TEXT PRIMARY KEY,
        pc_id TEXT,
        estado TEXT
    )
    """)

    # Usuario de prueba
    c.execute("""
    INSERT OR IGNORE INTO licencias (usuario, pc_id, estado)
    VALUES (?, ?, ?)
    """, ("franco", "154517002188928", "ACTIVO"))

    conn.commit()
    conn.close()

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "Servidor funcionando 🚀"

# =========================
# VERIFICAR LICENCIA
# =========================
@app.route("/verificar", methods=["GET"])
def verificar():
    user = request.args.get("user")
    pc = request.args.get("pc")

    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT pc_id, estado FROM licencias WHERE usuario = ?", (user,))
    row = c.fetchone()

    conn.close()

    if not row:
        return "BLOQUEADO"

    pc_db, estado = row

    if pc_db == pc and estado == "ACTIVO":
        return "ACTIVO"

    return "BLOQUEADO"

# =========================
# VER USUARIOS (API)
# =========================
@app.route("/usuarios")
def usuarios():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT usuario, pc_id, estado FROM licencias")
    data = c.fetchall()

    conn.close()

    return jsonify(data)

# =========================
# CAMBIAR ESTADO
# =========================
@app.route("/cambiar_estado", methods=["POST"])
def cambiar_estado():
    data = request.json
    user = data.get("user")
    estado = data.get("estado")

    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE licencias SET estado = ? WHERE usuario = ?", (estado, user))
    conn.commit()
    conn.close()

    return "OK"

@app.route("/test")
def test():
    return "FUNCIONA NUEVO CODIGO"

# =========================
# PANEL WEB
# =========================
@app.route("/panel")
def panel():
    return """
    <html>
    <body style="font-family: Arial; text-align:center; background:#f4f6f8;">
        <h2>Panel de Licencias</h2>

        <input id="user" placeholder="Usuario" style="padding:10px;"><br><br>

        <button onclick="activar()" style="padding:10px; background:green; color:white;">ACTIVAR</button>
        <button onclick="bloquear()" style="padding:10px; background:red; color:white;">BLOQUEAR</button>

        <br><br>
        <button onclick="cargar()">Ver Usuarios</button>

        <pre id="resultado"></pre>

        <script>
            function activar(){
                fetch('/cambiar_estado', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user: user.value, estado: 'ACTIVO'})
                }).then(()=>alert('Activado'));
            }

            function bloquear(){
                fetch('/cambiar_estado', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user: user.value, estado: 'BLOQUEADO'})
                }).then(()=>alert('Bloqueado'));
            }

            function cargar(){
                fetch('/usuarios')
                .then(res => res.json())
                .then(data => {
                    document.getElementById("resultado").innerText = JSON.stringify(data, null, 2);
                });
            }
        </script>
    </body>
    </html>
    """

# =========================
# RUN
# =========================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)