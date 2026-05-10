<<<<<<< HEAD
from dataclasses import dataclass
from typing import Dict

@dataclass
class AdaptiveThresholds:
    low: float = 0.0
    high: float = 1.0

def compute_score(metrics: Dict[str, float]) -> float:
    """Calcula um score simples para o MVP usando métricas como Alpha/Beta."""
    alpha = metrics.get("alpha", 0.0)
    beta = metrics.get("beta", 1.0)
    return alpha / (beta + 1e-5)

def adaptive_state(score: float, thresholds: AdaptiveThresholds) -> int:
    """Classifica o input baseado nos limites adaptativos."""
    if score > thresholds.high:
        return 1
    elif score < thresholds.low:
        return -1
    return 0
=======
from typing import Dict


def compute_score(features: Dict[str, float]) -> float:
    """
    Compute a scalar activation score from EEG-derived features.

    Weights:
      focus  -> 0.5  (primary intent signal)
      gamma  -> 0.3  (cognitive engagement)
      calm   -> 0.2  (inverse: low calm = high arousal)

    Returns a value in [0, 1].
    """
    focus = float(features.get("focus", 0.0))
    gamma = float(features.get("gamma", 0.0))
    calm = float(features.get("calm", 0.0))

    score = focus * 0.5 + gamma * 0.3 + (1.0 - calm) * 0.2
    return max(0.0, min(1.0, score))
>>>>>>> 531fc65123544157015ba2046c143129823abab2
