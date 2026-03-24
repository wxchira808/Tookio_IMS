"""
Risk ML Service for ARC System - KenTrade Tender KTNA/OT/04/2025-2026

Provides machine-learning-based risk analytics using Python standard ML libraries:
- Monte Carlo simulation for risk probability forecasting
- Scikit-learn based predictive risk scoring
- Historical trend analysis

Data Sovereignty: All computations run locally. No external API calls.
"""

# pyright: reportMissingImports=false

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Monte Carlo Risk Simulation
# ---------------------------------------------------------------------------

class MonteCarloRiskSimulator:
    """
    Runs Monte Carlo simulations to forecast risk occurrence probability
    and expected impact using likelihood/impact distributions.

    Compatible with ISO 31000 5x5 risk matrix scoring.
    """

    def __init__(self, n_simulations: int = 10_000, seed: int = 42):
        self.n_simulations = n_simulations
        self.seed = seed

    def simulate_risk(
        self,
        likelihood_mean: float,
        likelihood_std: float,
        impact_mean: float,
        impact_std: float,
        velocity_mean: float = 3.0,
        velocity_std: float = 0.5,
        control_effectiveness_mean: float = 3.0,
        control_effectiveness_std: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for a single risk.

        Parameters are means and standard deviations for the triangular
        distributions of each scoring dimension (scale 1-5).

        Returns probability distribution statistics for inherent and residual
        risk scores.
        """
        rng = random.Random(self.seed)

        inherent_scores: List[float] = []
        residual_scores: List[float] = []

        def clamp(val: float, lo: float = 1.0, hi: float = 5.0) -> float:
            return max(lo, min(hi, val))

        def gauss(mean: float, std: float) -> float:
            # Box-Muller transform for Normal distribution without numpy
            while True:
                u1 = rng.random()
                u2 = rng.random()
                if u1 > 0:
                    break
            z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            return mean + std * z

        for _ in range(self.n_simulations):
            l = clamp(gauss(likelihood_mean, likelihood_std))
            i = clamp(gauss(impact_mean, impact_std))
            v = clamp(gauss(velocity_mean, velocity_std))
            c = clamp(gauss(control_effectiveness_mean, control_effectiveness_std))

            inherent = l * i * v
            control_mod = (6.0 - c) / 5.0
            residual = inherent * control_mod

            inherent_scores.append(inherent)
            residual_scores.append(residual)

        return {
            "n_simulations": self.n_simulations,
            "inherent_risk": self._describe(inherent_scores),
            "residual_risk": self._describe(residual_scores),
            "probability_exceeds_threshold": {
                "50": self._prob_exceeds(residual_scores, 50),
                "75": self._prob_exceeds(residual_scores, 75),
                "100": self._prob_exceeds(residual_scores, 100),
            },
        }

    def simulate_portfolio(
        self, risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate aggregate risk portfolio score across multiple risks.

        Each risk in `risks` should have:
            likelihood, impact, velocity, control_effectiveness (all 1-5)
        """
        rng = random.Random(self.seed)
        portfolio_scores: List[float] = []

        for _ in range(self.n_simulations):
            total = 0.0
            for risk in risks:
                l = float(risk.get("likelihood", 3))
                i = float(risk.get("impact", 3))
                v = float(risk.get("velocity", 3))
                c = float(risk.get("control_effectiveness", 3))

                # Add noise proportional to uncertainty
                noise = lambda x: max(1, min(5, x + rng.gauss(0, 0.3)))
                total += noise(l) * noise(i) * noise(v) * ((6 - noise(c)) / 5)

            portfolio_scores.append(total)

        return {
            "n_risks": len(risks),
            "n_simulations": self.n_simulations,
            "portfolio_aggregate_score": self._describe(portfolio_scores),
        }

    @staticmethod
    def _describe(scores: List[float]) -> Dict[str, float]:
        if not scores:
            return {}
        n = len(scores)
        sorted_s = sorted(scores)
        mean = sum(scores) / n
        variance = sum((x - mean) ** 2 for x in scores) / n
        return {
            "mean": round(mean, 2),
            "std_dev": round(math.sqrt(variance), 2),
            "min": round(sorted_s[0], 2),
            "max": round(sorted_s[-1], 2),
            "p10": round(sorted_s[int(n * 0.10)], 2),
            "p25": round(sorted_s[int(n * 0.25)], 2),
            "p50": round(sorted_s[int(n * 0.50)], 2),
            "p75": round(sorted_s[int(n * 0.75)], 2),
            "p90": round(sorted_s[int(n * 0.90)], 2),
            "p95": round(sorted_s[int(n * 0.95)], 2),
        }

    @staticmethod
    def _prob_exceeds(scores: List[float], threshold: float) -> float:
        if not scores:
            return 0.0
        exceeded = sum(1 for s in scores if s > threshold)
        return round(exceeded / len(scores) * 100, 2)


# ---------------------------------------------------------------------------
# Scikit-learn based Risk Score Predictor
# ---------------------------------------------------------------------------

class RiskScorePredictor:
    """
    Predictive risk scoring model using scikit-learn (if available)
    with a pure-Python linear regression fallback.

    Trains on historical risk register data to predict future residual
    risk scores based on scoring dimensions.
    """

    def __init__(self):
        self._model = None
        self._sklearn_available = self._check_sklearn()

    @staticmethod
    def _check_sklearn() -> bool:
        try:
            import sklearn  # noqa: F401
            return True
        except ImportError:
            logger.info("scikit-learn not installed; using built-in linear regression fallback.")
            return False

    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train the predictive model on historical risk data.

        Each record should have: likelihood, impact, velocity,
        control_effectiveness, residual_risk_score.
        """
        if len(training_data) < 5:
            return {"status": "insufficient_data", "min_required": 5, "provided": len(training_data)}

        X, y = self._extract_features(training_data)

        if self._sklearn_available:
            return self._train_sklearn(X, y)
        return self._train_builtin(X, y)

    def predict(self, risk_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict residual risk score for a given set of features.
        Returns predicted score and confidence interval.
        """
        if self._model is None:
            return {"error": "Model not trained. Call train() first."}

        features = [
            float(risk_features.get("likelihood", 3)),
            float(risk_features.get("impact", 3)),
            float(risk_features.get("velocity", 3)),
            float(risk_features.get("control_effectiveness", 3)),
        ]

        if self._sklearn_available and hasattr(self._model, "predict"):
            import numpy as np
            predicted = float(self._model.predict(np.array([features]))[0])
        else:
            predicted = self._builtin_predict(features)

        return {
            "predicted_residual_score": round(predicted, 2),
            "risk_level": self._score_to_level(predicted),
        }

    @staticmethod
    def _extract_features(
        data: List[Dict[str, Any]]
    ) -> Tuple[List[List[float]], List[float]]:
        X, y = [], []
        for row in data:
            try:
                X.append([
                    float(row.get("likelihood", 3)),
                    float(row.get("impact", 3)),
                    float(row.get("velocity", 3)),
                    float(row.get("control_effectiveness", 3)),
                ])
                y.append(float(row.get("residual_risk_score", 0)))
            except (TypeError, ValueError):
                continue
        return X, y

    def _train_sklearn(self, X: List[List[float]], y: List[float]) -> Dict[str, Any]:
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import cross_val_score
        import numpy as np

        Xa = np.array(X)
        ya = np.array(y)

        self._model = Ridge(alpha=1.0)
        self._model.fit(Xa, ya)

        scores = cross_val_score(self._model, Xa, ya, cv=min(5, len(X)), scoring="r2")
        return {
            "status": "trained",
            "algorithm": "Ridge Regression (scikit-learn)",
            "n_samples": len(X),
            "cv_r2_mean": round(float(scores.mean()), 4),
            "cv_r2_std": round(float(scores.std()), 4),
        }

    def _train_builtin(self, X: List[List[float]], y: List[float]) -> Dict[str, Any]:
        """Simple ordinary least-squares linear regression (no dependencies)."""
        n = len(y)
        k = len(X[0])
        # Simple mean-based coefficients (first-order approximation)
        means_x = [sum(row[j] for row in X) / n for j in range(k)]
        mean_y = sum(y) / n

        # Compute regression coefficients via normal equations (simplified)
        coefs = []
        for j in range(k):
            num = sum((X[i][j] - means_x[j]) * (y[i] - mean_y) for i in range(n))
            denom = sum((X[i][j] - means_x[j]) ** 2 for i in range(n))
            coefs.append(num / denom if denom != 0 else 0)

        intercept = mean_y - sum(c * m for c, m in zip(coefs, means_x))
        self._model = {"coefs": coefs, "intercept": intercept, "means_x": means_x}

        # R² score
        ss_res = sum((y[i] - self._builtin_predict(X[i])) ** 2 for i in range(n))
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

        return {
            "status": "trained",
            "algorithm": "Linear Regression (built-in)",
            "n_samples": n,
            "r2_score": round(r2, 4),
        }

    def _builtin_predict(self, features: List[float]) -> float:
        if isinstance(self._model, dict):
            coefs = self._model["coefs"]
            intercept = self._model["intercept"]
            return intercept + sum(c * f for c, f in zip(coefs, features))
        return 0.0

    @staticmethod
    def _score_to_level(score: float) -> str:
        if score >= 80:
            return "Very High"
        if score >= 50:
            return "High"
        if score >= 25:
            return "Medium"
        if score >= 10:
            return "Low"
        return "Very Low"


# ---------------------------------------------------------------------------
# Frappe-callable API functions
# ---------------------------------------------------------------------------

def run_monte_carlo_simulation(
    likelihood: float,
    impact: float,
    velocity: float = 3.0,
    control_effectiveness: float = 3.0,
    n_simulations: int = 10_000,
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation for a single risk.
    Callable from Frappe server scripts or whitelisted API.

    Parameters match IMS Risk Register scoring fields (scale 1-5).
    """
    simulator = MonteCarloRiskSimulator(n_simulations=n_simulations)
    return simulator.simulate_risk(
        likelihood_mean=likelihood,
        likelihood_std=0.5,
        impact_mean=impact,
        impact_std=0.5,
        velocity_mean=velocity,
        velocity_std=0.3,
        control_effectiveness_mean=control_effectiveness,
        control_effectiveness_std=0.3,
    )


def run_portfolio_simulation(risks: List[Dict[str, Any]], n_simulations: int = 10_000) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation across a portfolio of risks.
    `risks` is a list of dicts with likelihood, impact, velocity, control_effectiveness keys.
    """
    simulator = MonteCarloRiskSimulator(n_simulations=n_simulations)
    return simulator.simulate_portfolio(risks)


def train_risk_predictor(training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Train the risk score predictor on historical data from IMS Risk Register."""
    predictor = RiskScorePredictor()
    result = predictor.train(training_data)
    # Store predictor state for later predictions (in-memory for now)
    _PREDICTOR_REGISTRY["default"] = predictor
    return result


def predict_risk_score(
    likelihood: float,
    impact: float,
    velocity: float = 3.0,
    control_effectiveness: float = 3.0,
) -> Dict[str, Any]:
    """Predict residual risk score using trained model."""
    predictor = _PREDICTOR_REGISTRY.get("default")
    if not predictor or predictor._model is None:
        return {"error": "Predictor not trained. Call train_risk_predictor first."}
    return predictor.predict({
        "likelihood": likelihood,
        "impact": impact,
        "velocity": velocity,
        "control_effectiveness": control_effectiveness,
    })


def get_risk_probability_summary(risk_register_name: str) -> Dict[str, Any]:
    """
    Fetch a risk from IMS Risk Register and run a Monte Carlo simulation.
    Returns probability distribution for board reporting.
    """
    try:
        import frappe
        risk = frappe.get_doc("IMS Risk Register", risk_register_name)
        result = run_monte_carlo_simulation(
            likelihood=float(risk.likelihood or 3),
            impact=float(risk.impact or 3),
            velocity=float(risk.velocity or 3),
            control_effectiveness=float(risk.control_effectiveness or 3),
        )
        result["risk_name"] = risk_register_name
        result["risk_title"] = risk.risk_title
        result["current_risk_level"] = risk.risk_level
        return result
    except Exception as e:
        return {"error": str(e)}


# Global predictor registry (in-process; use a cache or DB for persistence)
_PREDICTOR_REGISTRY: Dict[str, RiskScorePredictor] = {}
