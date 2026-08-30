"""
Recovery probability ranker using XGBoost.
"""
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from config.settings import settings
from config.logger import logger

class RecoveryRanker:
    FEATURES = [
        "amount_paise",
        "day_of_month",
        "cycle_number",
        "prior_broken_ptps",
        "customer_tenure_days",
        "last_success_days_ago",
        "is_funds_class",
        "is_downtime_class",
        "is_mandate_dead",
        "is_instrument_dead",
        "is_limit_class",
        "attempts_so_far",
        "has_prior_contact",
    ]

    def __init__(self, model_path=None):
        self.model = None
        if model_path and model_path.exists():
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            logger.info(f"Loaded ranker from {model_path}")
        else:
            logger.warning("No pre-trained ranker found. Will train on the fly or use heuristic.")

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train an XGBoost classifier."""
        from xgboost import XGBClassifier
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="binary:logistic",
            eval_metric="auc",
            random_state=42
        )
        self.model.fit(X, y)

    def predict_proba(self, event_features: Dict[str, Any]) -> float:
        """Return probability of recovery given features."""
        if self.model is None:
            # Fallback heuristic if no model: use simple rules based on class
            return self._heuristic_proba(event_features)
        # Create feature vector in correct order
        X = self._build_feature_vector(event_features)
        proba = self.model.predict_proba(X)[0, 1]
        return float(proba)

    def _build_feature_vector(self, event_features: Dict[str, Any]) -> np.ndarray:
        """Convert dict to numpy array aligned with FEATURES."""
        features = []
        for f in self.FEATURES:
            features.append(event_features.get(f, 0))
        return np.array(features).reshape(1, -1)

    def _heuristic_proba(self, features: Dict[str, Any]) -> float:
        """Simple heuristic used if no model is trained."""
        # Map class to base probability
        if features.get("is_funds_class"):
            base = 0.45
        elif features.get("is_downtime_class"):
            base = 0.70
        elif features.get("is_mandate_dead"):
            base = 0.30
        elif features.get("is_instrument_dead"):
            base = 0.20
        elif features.get("is_limit_class"):
            base = 0.10
        else:
            base = 0.05
        # Adjust based on attempts
        if features.get("attempts_so_far", 0) > 0:
            base *= 0.7
        return min(base, 0.95)