from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔥 "Base de datos" simple (después la podés mejorar)
usuarios = {
    "franco": {
        "pc_id": "154517002188928",
        "estado": "ACTIVO"
    },
    "cliente1": {
        "pc_id": "99999",
        "estado": "BLOQUEADO"
    }
}

@app.route("/verificar", methods=["GET"])
def verificar():
    user = request.args.get("user")
    pc = request.args.get("pc")

    if user in usuarios:
        if usuarios[user]["pc_id"] == pc:
            return usuarios[user]["estado"]
    
    return "BLOQUEADO"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)