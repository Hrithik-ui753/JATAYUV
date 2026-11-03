import numpy as np
import torch
from typing import Dict, Any, List, Optional, Tuple

class ConfusionMatrix:
    """Maintains a confusion matrix for multiclass or binary evaluation."""
    def __init__(self, num_classes: int):
        self.num_classes = num_classes
        self.matrix = np.zeros((num_classes, num_classes), dtype=np.int64)

    def update(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Update confusion matrix with batch predictions and ground truth.
        Row index: true label
        Column index: predicted label
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        
        valid = (y_true >= 0) & (y_true < self.num_classes) & (y_pred >= 0) & (y_pred < self.num_classes)
        y_true = y_true[valid]
        y_pred = y_pred[valid]
        
        indices = self.num_classes * y_true + y_pred
        counts = np.bincount(indices, minlength=self.num_classes ** 2)
        self.matrix += counts.reshape(self.num_classes, self.num_classes)

    def reset(self):
        self.matrix.fill(0)


def compute_segmentation_metrics(
    cm: np.ndarray,
    class_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes real semantic segmentation metrics from confusion matrix:
    - Pixel accuracy
    - Per-class IoU & Mean IoU (mIoU)
    - Per-class Precision & Macro Precision
    - Per-class Recall & Macro Recall
    """
    num_classes = cm.shape[0]
    if class_names is None:
        class_names = [f"Class_{i}" for i in range(num_classes)]

    total_pixels = int(np.sum(cm))
    correct_pixels = int(np.trace(cm))
    pixel_accuracy = float(correct_pixels / max(total_pixels, 1))

    per_class_iou = {}
    per_class_precision = {}
    per_class_recall = {}
    ious = []
    precisions = []
    recalls = []

    for c in range(num_classes):
        name = class_names[c] if c < len(class_names) else f"Class_{c}"
        tp = float(cm[c, c])
        fn = float(np.sum(cm[c, :]) - tp)
        fp = float(np.sum(cm[:, c]) - tp)

        denom_iou = tp + fp + fn
        iou = float(tp / denom_iou) if denom_iou > 0 else 0.0
        
        denom_prec = tp + fp
        precision = float(tp / denom_prec) if denom_prec > 0 else 0.0
        
        denom_rec = tp + fn
        recall = float(tp / denom_rec) if denom_rec > 0 else 0.0

        per_class_iou[name] = round(iou, 4)
        per_class_precision[name] = round(precision, 4)
        per_class_recall[name] = round(recall, 4)

        ious.append(iou)
        precisions.append(precision)
        recalls.append(recall)

    mean_iou = float(np.mean(ious)) if len(ious) > 0 else 0.0
    macro_precision = float(np.mean(precisions)) if len(precisions) > 0 else 0.0
    macro_recall = float(np.mean(recalls)) if len(recalls) > 0 else 0.0

    return {
        "pixel_accuracy": round(pixel_accuracy, 4),
        "mean_iou": round(mean_iou, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "per_class_iou": per_class_iou,
        "per_class_precision": per_class_precision,
        "per_class_recall": per_class_recall,
        "confusion_matrix": cm.tolist()
    }


def compute_damage_metrics(
    cm: np.ndarray,
    damage_classes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes disaster building damage assessment metrics according to xBD/xView2 specs:
    - Macro-F1 across damage classes
    - Per-class precision
    - Per-class recall
    - Per-class F1
    - Confusion matrix
    """
    num_classes = cm.shape[0]
    if damage_classes is None:
        damage_classes = ["no-damage", "minor-damage", "major-damage", "destroyed"]

    per_class_precision = {}
    per_class_recall = {}
    per_class_f1 = {}
    f1_scores = []

    for c in range(num_classes):
        name = damage_classes[c] if c < len(damage_classes) else f"Damage_{c}"
        tp = float(cm[c, c])
        fn = float(np.sum(cm[c, :]) - tp)
        fp = float(np.sum(cm[:, c]) - tp)

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * (prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_class_precision[name] = round(prec, 4)
        per_class_recall[name] = round(rec, 4)
        per_class_f1[name] = round(f1, 4)
        f1_scores.append(f1)

    macro_f1 = float(np.mean(f1_scores)) if len(f1_scores) > 0 else 0.0

    return {
        "macro_f1": round(macro_f1, 4),
        "per_class_precision": per_class_precision,
        "per_class_recall": per_class_recall,
        "per_class_f1": per_class_f1,
        "confusion_matrix": cm.tolist()
    }


def compute_change_detection_metrics(cm: np.ndarray) -> Dict[str, Any]:
    """
    Computes binary change detection metrics (LEVIR-CD standard):
    Positive class is 1 (Changed), negative is 0 (Unchanged).
    - Precision
    - Recall
    - F1
    - IoU
    """
    # cm: [2x2], [0,0]=TN, [0,1]=FP, [1,0]=FN, [1,1]=TP
    tp = float(cm[1, 1]) if cm.shape == (2, 2) else 0.0
    fp = float(cm[0, 1]) if cm.shape == (2, 2) else 0.0
    fn = float(cm[1, 0]) if cm.shape == (2, 2) else 0.0
    tn = float(cm[0, 0]) if cm.shape == (2, 2) else 0.0

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0
    iou = float(tp / (tp + fp + fn)) if (tp + fp + fn) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "iou": round(iou, 4),
        "confusion_matrix": cm.tolist()
    }
