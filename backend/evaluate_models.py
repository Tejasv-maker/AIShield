import pandas as pd
import joblib
import os

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
    roc_auc_score
)

os.makedirs(
    "reports/ml",
    exist_ok=True
)

df = pd.read_csv(
    "data/sms_dataset.csv"
)

df = df.dropna()

X = df["text"].astype(str)

y = df["label"].map({
    "ham": 0,
    "spam": 1
})

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=.25,
    random_state=42,
    stratify=y
)

model = joblib.load(
    "ml/models/text_model.pkl"
)

predictions = model.predict(X_test)

probabilities = model.predict_proba(
    X_test
)[:, 1]


# -----------------------------
# CONFUSION MATRIX
# -----------------------------

cm = confusion_matrix(
    y_test,
    predictions
)

display = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=[
        "Safe",
        "Threat"
    ]
)

display.plot()

plt.title(
    "AIShield Confusion Matrix"
)

plt.savefig(
    "reports/ml/confusion_matrix.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# -----------------------------
# ROC CURVE
# -----------------------------

fpr, tpr, thresholds = roc_curve(
    y_test,
    probabilities
)

auc = roc_auc_score(
    y_test,
    probabilities
)

plt.figure()

plt.plot(
    fpr,
    tpr,
    label=f"AIShield AUC = {auc:.3f}"
)

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--"
)

plt.xlabel(
    "False Positive Rate"
)

plt.ylabel(
    "True Positive Rate"
)

plt.title(
    "AIShield ROC Curve"
)

plt.legend()

plt.savefig(
    "reports/ml/roc_curve.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print(
    f"ROC-AUC: {auc:.4f}"
)

print(
    "Evaluation reports generated."
)