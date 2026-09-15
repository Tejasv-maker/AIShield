import joblib
import os

MODEL_PATH = "ml/models/text_model.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "Text model not found. Run ml/train_text_model.py first."
    )

model = joblib.load(MODEL_PATH)


def analyze_text(text):

    if not text or not text.strip():
        return {
            "label": "Unknown",
            "risk": 0,
            "confidence": 0,
            "reasons": []
        }

    probability = model.predict_proba([text])[0][1]

    risk = round(probability * 100, 2)

    if risk >= 70:
        label = "High Risk"
    elif risk >= 40:
        label = "Suspicious"
    else:
        label = "Safe"

    reasons = []

    suspicious_words = [
        "urgent",
        "verify",
        "verification",
        "winner",
        "won",
        "prize",
        "claim",
        "free",
        "reward",
        "password",
        "account",
        "bank",
        "click",
        "limited",
        "offer",
        "cash"
    ]

    text_lower = text.lower()

    for word in suspicious_words:
        if word in text_lower:
            reasons.append(
                f"Suspicious keyword detected: '{word}'"
            )

    if "http://" in text_lower or "https://" in text_lower:
        reasons.append("Message contains a web link.")

    if "!" in text:
        reasons.append("Excessive promotional/urgent punctuation.")

    if not reasons:
        reasons.append(
            "No strong suspicious indicators detected."
        )

    return {
        "label": label,
        "risk": risk,
        "confidence": round(max(probability, 1 - probability) * 100, 2),
        "reasons": reasons[:5]
    }