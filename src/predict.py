"""Load model bundle and return aligned predictions for review and delivery risk."""
from __future__ import annotations
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from src import config, features


def load_bundle():
    """Load the saved classifier/regressor bundle from models/review_model.pkl."""
    path = Path(config.MODEL_FILE)
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}. Run python -m src.train_model first.")
    saved = joblib.load(path)
    if isinstance(saved, dict) and "classifier" in saved:
        return saved
    # Backward compatibility with an older artifact containing only a classifier.
    return {"classifier": saved, "regressor": None, "late_classifier": None, "delivery_regressor": None,
            "feature_columns": features.FEATURE_COLUMNS, "metrics": {}, "odds_ratios": []}


def bundle():
    """Backward-compatible bundle loader for existing Streamlit pages."""
    return load_bundle()


def load_model():
    return load_bundle()["classifier"]


def predict_review_risk(input_data, model=None):
    """Predict the probability of a not-satisfied review (score 1–3).

    If the saved bundle contains supporting models, also estimates late-delivery
    probability and delivery duration for the same order-time feature inputs.
    """
    saved = model if isinstance(model, dict) and "classifier" in model else None
    classifier = saved["classifier"] if saved else (model if model is not None else load_model())
    if isinstance(input_data, pd.DataFrame):
        row = input_data.copy()
    else:
        row = features.prediction_row(input_data)
    expected = saved.get("feature_columns", features.FEATURE_COLUMNS) if saved else features.FEATURE_COLUMNS
    row = row.reindex(columns=expected)

    prediction = int(classifier.predict(row)[0])
    class_probabilities = classifier.predict_proba(row)[0]
    classes = list(classifier.classes_)
    positive_index = classes.index(1) if 1 in classes else min(1, len(class_probabilities) - 1)
    probability = float(class_probabilities[positive_index])

    score_prediction = None
    late_probability = None
    predicted_delivery_days = None
    if saved:
        review_regressor = saved.get("regressor")
        late_classifier = saved.get("late_classifier")
        delivery_regressor = saved.get("delivery_regressor")
        if review_regressor is not None:
            score_prediction = float(np.clip(review_regressor.predict(row)[0], 1, 5))
        if late_classifier is not None:
            late_probs = late_classifier.predict_proba(row)[0]
            late_classes = list(late_classifier.classes_)
            late_index = late_classes.index(1) if 1 in late_classes else min(1, len(late_probs) - 1)
            late_probability = float(late_probs[late_index])
        if delivery_regressor is not None:
            predicted_delivery_days = float(max(0, delivery_regressor.predict(row)[0]))

    return {
        "prediction": prediction,
        "label": "Not satisfied (review score 1–3)" if prediction == 1 else "Satisfied (review score 4–5)",
        "probability": probability,
        "probability_percent": probability * 100,
        "predicted_review_score": score_prediction,
        "late_probability": late_probability,
        "late_probability_percent": late_probability * 100 if late_probability is not None else None,
        "predicted_delivery_days": predicted_delivery_days,
    }


def predict_order(input_data, model=None):
    return predict_review_risk(input_data, model=model)


def predict_low_review(input_data, model=None):
    return predict_review_risk(input_data, model=model)


def predict_probability(input_data, model=None):
    return predict_review_risk(input_data, model=model)["probability"]
