"""Leakage-aware evaluation and operational anomaly monitoring."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, average_precision_score, balanced_accuracy_score, confusion_matrix, matthews_corrcoef, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate

RANDOM_STATE = 42


def _folds(labels):
    counts = pd.Series(labels).value_counts()
    return min(5, int(counts.min())) if not counts.empty else 0


def _empty_classification():
    return {"macro_precision": None, "macro_recall": None, "macro_f1": None, "balanced_accuracy": None, "weighted_f1": None, "accuracy": None, "mcc": None, "per_class": [], "confusion": None, "expected": None, "predicted": None, "output_labels": None, "confidence": None, "cv": None, "samples": 0}


def _anomaly_truth(values):
    values = pd.Series(values)
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.eq(1) if numeric.notna().all() else values.astype(str).str.lower().str.strip().isin(["1", "true", "yes", "anomaly"])


def _classification_summary(actual, predicted, probabilities, cv_scores):
    actual, predicted = pd.Series(actual).astype(str), pd.Series(predicted).astype(str)
    labels = sorted(set(actual) | set(predicted))
    p, r, f, support = precision_recall_fscore_support(actual, predicted, labels=labels, zero_division=0)
    mp, mr, mf1, _ = precision_recall_fscore_support(actual, predicted, average="macro", zero_division=0)
    _, _, wf1, _ = precision_recall_fscore_support(actual, predicted, average="weighted", zero_division=0)
    confidence = np.asarray(probabilities).max(axis=1)
    mapping = {label: index for index, label in enumerate(labels)}
    return {"macro_precision": float(mp), "macro_recall": float(mr), "macro_f1": float(mf1), "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)), "weighted_f1": float(wf1), "accuracy": float(accuracy_score(actual, predicted)), "mcc": float(matthews_corrcoef(actual, predicted)), "per_class": [{"label": label, "precision": float(x), "recall": float(y), "f1": float(z), "support": int(s)} for label, x, y, z, s in zip(labels, p, r, f, support)], "confusion": (labels, confusion_matrix(actual, predicted, labels=labels).tolist()), "expected": [mapping[x] for x in actual], "predicted": [mapping[x] for x in predicted], "output_labels": labels, "confidence": {"mean": float(confidence.mean()), "median": float(np.median(confidence)), "std": float(confidence.std()), "min": float(confidence.min()), "max": float(confidence.max()), "values": confidence.tolist()}, "cv": {name: {"mean": float(np.mean(values)), "std": float(np.std(values)), "values": values.tolist()} for name, values in cv_scores.items()}, "samples": len(actual)}


def evaluate_models(features, risk_labels, anomaly_labels=None):
    """Use shuffled, fixed-seed stratified CV; do not infer anomaly truth."""
    result = {"classification": _empty_classification(), "anomaly": None, "classification_method": "Unavailable: every risk class needs at least two labels.", "anomaly_method": "Operational anomaly monitoring — independently validated anomaly labels unavailable.", "anomaly_monitoring": None}
    X, actual = features.fillna(0), pd.Series(risk_labels).astype(str).reset_index(drop=True)
    folds = _folds(actual)
    if folds >= 2:
        cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
        model = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=RANDOM_STATE)
        probabilities = cross_val_predict(model, X, actual, cv=cv, method="predict_proba")
        classes = np.sort(actual.unique())
        predictions = classes[probabilities.argmax(axis=1)]
        scores = cross_validate(model, X, actual, cv=cv, scoring={"macro_f1": "f1_macro", "balanced_accuracy": "balanced_accuracy", "weighted_f1": "f1_weighted"})
        result["classification"] = _classification_summary(actual, predictions, probabilities, {key[5:]: value for key, value in scores.items() if key.startswith("test_")})
        result["classification_method"] = f"{folds}-fold stratified cross-validation (shuffle=True, random_state={RANDOM_STATE})"
    if anomaly_labels is not None:
        actual = _anomaly_truth(anomaly_labels).reset_index(drop=True)
        folds = _folds(actual)
        if folds >= 2:
            cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
            predictions = np.empty(len(X), dtype=int)
            scores = np.empty(len(X), dtype=float)
            for train_index, test_index in cv.split(X, actual):
                model = IsolationForest(contamination="auto", random_state=RANDOM_STATE)
                model.fit(X.iloc[train_index])
                predictions[test_index] = model.predict(X.iloc[test_index])
                scores[test_index] = -model.decision_function(X.iloc[test_index])
            predicted = pd.Series(predictions).eq(-1)
            p, r, f, _ = precision_recall_fscore_support(actual, predicted, average="binary", zero_division=0)
            result["anomaly"] = {"precision": float(p), "recall": float(r), "f1": float(f), "pr_auc": float(average_precision_score(actual, scores)), "roc_auc": float(roc_auc_score(actual, scores)), "false_positive_rate": float((predicted & ~actual).sum() / max((~actual).sum(), 1)), "confusion": (["Normal", "Anomaly"], confusion_matrix(actual, predicted, labels=[False, True]).tolist()), "expected": actual.astype(int).tolist(), "predicted": predicted.astype(int).tolist(), "output_labels": ["Normal", "Anomaly"], "samples": len(actual)}
            result["anomaly_method"] = f"{folds}-fold stratified cross-validation against supplied is_anomaly labels"
        else:
            result["anomaly_method"] = "Unavailable: anomaly and normal labels each need at least two rows."
    return result


def add_anomaly_monitoring(evaluation, data):
    frame = pd.DataFrame(data)
    scores, labels = pd.to_numeric(frame["anomaly_score"], errors="coerce"), pd.to_numeric(frame["anomaly_label"], errors="coerce")
    columns = [x for x in ["protocol_version", "key_exchange_algorithm", "key_size", "cipher_suite", "anomaly_score"] if x in frame]
    top20 = frame.loc[:, columns].assign(anomaly_score=scores).nlargest(20, "anomaly_score")
    evaluation["anomaly_monitoring"] = {"detected": int((labels == -1).sum()), "alert_rate": float((labels == -1).mean()), "mean": float(scores.mean()), "median": float(scores.median()), "std": float(scores.std()), "min": float(scores.min()), "max": float(scores.max()), "p95": float(scores.quantile(.95)), "values": scores.dropna().tolist(), "top20": top20.to_dict("records"), "samples": len(frame)}
    return evaluation
