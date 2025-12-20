from backend import access_person as ap
from flask import Flask , request , render_template , send_file , abort
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/verify")
def verify():
    roll = request.args.get("roll")
    if not roll:
        return "Invalid QR code", 400

    roll = roll.lower()

    data = ap.get_user_by_reg(roll)

    if data.empty:
        return render_template("verify.html", status="invalid")

    return render_template(
        "verify.html",
        status="valid",
        roll=roll,
        records=data.to_dict(orient="records")
    )

@app.route("/download")
def download():
    roll = request.args.get("roll")
    event = request.args.get("event")

    path = f"backend/certificates/{roll}_{event.replace(' ', '_')}.png"

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)