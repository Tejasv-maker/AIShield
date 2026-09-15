from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
import sys
import traceback
import joblib


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =========================================================
# BACKEND IMPORTS
# =========================================================

try:
    from backend.feature_extraction import extract_features
    from backend.text_model import analyze_text
    from backend.report_generator import create_report

except ModuleNotFoundError as error:
    print("\n" + "=" * 60)
    print("AIShield BACKEND IMPORT ERROR")
    print("=" * 60)
    print(f"\nError: {error}\n")
    print("Required structure:")
    print("""
AIShield/
│
├── app.py
│
├── backend/
│   ├── __init__.py
│   ├── feature_extraction.py
│   ├── text_model.py
│   └── report_generator.py
│
├── ml/
│   └── models/
│       ├── url_model.pkl
│       └── text_model.pkl
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
""")
    print("=" * 60)
    raise


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


# =========================================================
# MODEL PATHS
# =========================================================

URL_MODEL_PATH = os.path.join(
    BASE_DIR, "ml", "models", "url_model.pkl"
)

OLD_URL_MODEL_PATH = os.path.join(
    BASE_DIR, "model", "phishing_model.pkl"
)


# =========================================================
# LOAD URL MODEL
# =========================================================

url_model = None

if os.path.exists(URL_MODEL_PATH):
    try:
        url_model = joblib.load(URL_MODEL_PATH)
        print("[OK] URL model loaded:")
        print(f"     {URL_MODEL_PATH}")
    except Exception as error:
        print("[ERROR] URL model could not be loaded.")
        print(error)

elif os.path.exists(OLD_URL_MODEL_PATH):
    try:
        url_model = joblib.load(OLD_URL_MODEL_PATH)
        print("[OK] Old URL model loaded:")
        print(f"     {OLD_URL_MODEL_PATH}")
        print("\n[WARNING] Recommended model location:")
        print(URL_MODEL_PATH)
    except Exception as error:
        print("[ERROR] Old URL model could not be loaded.")
        print(error)

else:
    print("\n" + "=" * 60)
    print("WARNING: URL MODEL NOT FOUND")
    print("=" * 60)
    print("\nExpected location:")
    print(URL_MODEL_PATH)
    print("\nOld supported location:")
    print(OLD_URL_MODEL_PATH)
    print("\nURL scanning will return an error until")
    print("the URL model is trained.")
    print("=" * 60)


# =========================================================
# DATABASE
# =========================================================

DATABASE = os.path.join(BASE_DIR, "threat_history.db")


def get_db():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT NOT NULL,
            content TEXT NOT NULL,
            result TEXT NOT NULL,
            risk REAL NOT NULL,
            confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


init_db()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def classify_risk(score):
    score = float(score)

    if score < 50:
        return "Safe"
    elif score < 75:
        return "Suspicious"
    else:
        return "High Risk"


def save_scan(scan_type, content, result, risk, confidence):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO scans
        (
            scan_type,
            content,
            result,
            risk,
            confidence
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        scan_type,
        content,
        result,
        risk,
        confidence
    ))

    connection.commit()
    connection.close()


def get_url_reasons(features):
    reasons = []

    try:
        feature_list = list(features)

        if len(feature_list) >= 1 and feature_list[0] > 75:
            reasons.append("URL is unusually long.")

        if len(feature_list) >= 3 and feature_list[2] > 3:
            reasons.append("Multiple dots detected in the URL.")

        if len(feature_list) >= 4 and feature_list[3] > 2:
            reasons.append("Multiple hyphens detected.")

        if len(feature_list) >= 5 and feature_list[4] == 1:
            reasons.append("@ symbol detected in URL.")

        if len(feature_list) >= 10 and feature_list[9] == 0:
            reasons.append("HTTPS security indicator is missing.")

        if len(feature_list) >= 12 and feature_list[11] > 0:
            reasons.append("Suspicious keywords detected.")

        if len(feature_list) >= 13 and feature_list[12] == 1:
            reasons.append(
                "Possible IP address detected instead of a normal domain."
            )

    except Exception as error:
        print("URL REASON ERROR:", error)

    if not reasons:
        reasons.append(
            "No major suspicious URL indicators detected."
        )

    return reasons


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# URL SCANNER
# =========================================================

@app.route("/api/scan", methods=["POST"])
def scan_url():
    try:
        if url_model is None:
            return jsonify({
                "success": False,
                "error": (
                    "URL model not found. "
                    "Please train the URL model first."
                )
            }), 500

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request."
            }), 400

        url = str(data.get("url", "")).strip()

        if not url:
            return jsonify({
                "success": False,
                "error": "Please enter a URL."
            }), 400

        # Add a scheme only for model parsing.
        if not (
            url.lower().startswith("http://")
            or url.lower().startswith("https://")
        ):
            url_for_model = "http://" + url
        else:
            url_for_model = url

        # Feature extraction
        features = extract_features(url_for_model)

        # Helpful compatibility check
        expected_features = getattr(
            url_model, "n_features_in_", None
        )

        if expected_features is not None:
            if len(features) != int(expected_features):
                return jsonify({
                    "success": False,
                    "error": (
                        "URL model expects "
                        f"{expected_features} features, but the "
                        f"current feature extractor produced "
                        f"{len(features)}. Please retrain the URL "
                        "model using the current feature_extraction.py."
                    )
                }), 500

        # ML prediction
        prediction = url_model.predict([features])[0]
        probabilities = url_model.predict_proba([features])[0]

        classes = list(
            getattr(url_model, "classes_", [])
        )

        # Calculate phishing probability
        if 1 in classes:
            phishing_index = classes.index(1)
            risk = probabilities[phishing_index] * 100

        elif "phishing" in classes:
            phishing_index = classes.index("phishing")
            risk = probabilities[phishing_index] * 100

        elif "Phishing" in classes:
            phishing_index = classes.index("Phishing")
            risk = probabilities[phishing_index] * 100

        else:
            # Generic binary fallback
            try:
                prediction_is_threat = int(prediction) == 1
            except (TypeError, ValueError):
                prediction_is_threat = str(prediction).lower() in {
                    "phishing", "spam", "malicious", "1", "true"
                }

            if prediction_is_threat:
                risk = max(probabilities) * 100
            else:
                risk = (1 - max(probabilities)) * 100

        risk = round(float(risk), 2)

        label = classify_risk(risk)

        confidence = round(
            float(max(probabilities)) * 100,
            2
        )

        reasons = get_url_reasons(features)

        # Save result
        save_scan(
            "URL",
            url,
            label,
            risk,
            confidence
        )

        return jsonify({
            "success": True,
            "type": "URL",
            "content": url,
            "label": label,
            "risk": risk,
            "confidence": confidence,
            "reasons": reasons,
            "features": features
        })

    except Exception as error:
        print("\n========== URL SCAN ERROR ==========")
        print("ERROR:", repr(error))
        traceback.print_exc()
        print("====================================\n")

        return jsonify({
            "success": False,
            "error": f"URL analysis error: {str(error)}"
        }), 500


# =========================================================
# SMS / EMAIL SCANNER
# =========================================================

@app.route("/api/scan-text", methods=["POST"])
def scan_text():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400

        text = str(data.get("text", "")).strip()
        scan_type = str(data.get("type", "sms")).strip().lower()

        if not text:
            return jsonify({
                "success": False,
                "error": "Text is required"
            }), 400

        # AI text analysis
        result = analyze_text(text)

        risk = round(
            float(result.get("risk", 0)),
            2
        )

        confidence = round(
            float(result.get("confidence", 0)),
            2
        )

        # Final classification based on risk score
        if risk < 50:
            label = "Safe"
        elif risk < 75:
            label = "Suspicious"
        else:
            label = "High Risk"

        reasons = result.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        save_scan(
            scan_type,
            text,
            label,
            risk,
            confidence
        )

        return jsonify({
            "success": True,
            "type": scan_type,
            "content": text,
            "label": label,
            "risk": risk,
            "confidence": confidence,
            "reasons": reasons
        })

    except Exception as e:
        print("TEXT SCAN ERROR:")
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================================================
# SCAN HISTORY
# =========================================================

@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        connection = get_db()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                scan_type,
                content,
                result,
                risk,
                confidence,
                created_at
            FROM scans
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()
        connection.close()

        history = []

        for row in rows:
            history.append({
                "id": row["id"],
                "type": row["scan_type"],
                "content": row["content"],
                "result": row["result"],
                "risk": row["risk"],
                "confidence": row["confidence"],
                "created_at": row["created_at"]
            })

        return jsonify(history)

    except Exception as error:
        print("\n========== HISTORY ERROR ==========")
        print("ERROR:", repr(error))
        traceback.print_exc()
        print("===================================\n")

        return jsonify({
            "success": False,
            "error": "Unable to load history."
        }), 500


# =========================================================
# SECURITY REPORT
# =========================================================

@app.route("/api/report", methods=["POST"])
def generate_security_report():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid report request."
            }), 400

        scan_type = str(data.get("type", "Unknown"))
        content = str(data.get("content", ""))
        label = str(data.get("label", "Unknown"))

        risk = float(data.get("risk", 0))
        confidence = float(data.get("confidence", 0))

        reasons = data.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        os.makedirs(
            os.path.join(BASE_DIR, "reports"),
            exist_ok=True
        )

        filename = create_report(
            scan_type,
            content,
            label,
            risk,
            confidence,
            reasons
        )

        if not filename:
            return jsonify({
                "success": False,
                "error": "Report file was not created."
            }), 500

        # Handle relative paths returned by report_generator.py
        if not os.path.isabs(filename):
            filename = os.path.join(BASE_DIR, filename)

        if not os.path.exists(filename):
            return jsonify({
                "success": False,
                "error": "Report file was not created."
            }), 500

        return send_file(
            filename,
            as_attachment=True,
            download_name="AIShield_Security_Report.pdf",
            mimetype="application/pdf"
        )

    except Exception as error:
        print("\n========== REPORT ERROR ==========")
        print("ERROR:", repr(error))
        traceback.print_exc()
        print("==================================\n")

        return jsonify({
            "success": False,
            "error": f"Report generation error: {str(error)}"
        }), 500


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        connection = get_db()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
        """)
        total_scans = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE result = 'Safe'
        """)
        safe_scans = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE result = 'High Risk'
        """)
        threats = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE result = 'Suspicious'
        """)
        suspicious = cursor.fetchone()[0]

        connection.close()

        return jsonify({
            "total_scans": total_scans,
            "safe_scans": safe_scans,
            "threats": threats,
            "suspicious": suspicious
        })

    except Exception as error:
        print("\n========== STATS ERROR ==========")
        print("ERROR:", repr(error))
        traceback.print_exc()
        print("=================================\n")

        return jsonify({
            "success": False,
            "error": "Unable to load statistics."
        }), 500


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "application": "AIShield",
        "url_model": url_model is not None,
        "database": os.path.exists(DATABASE)
    })


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("        AIShield Cyber Intelligence System")
    print("=" * 60)
    print()
    print("Project:")
    print(BASE_DIR)
    print()
    print(
        "URL Model:",
        "READY" if url_model is not None else "NOT FOUND"
    )
    print()
    print("Database:")
    print(DATABASE)
    print()
    print("Server running at:")
    print("http://127.0.0.1:5000")
    print()
    print("Health check:")
    print("http://127.0.0.1:5000/api/health")
    print()
    print("Press CTRL+C to stop.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
