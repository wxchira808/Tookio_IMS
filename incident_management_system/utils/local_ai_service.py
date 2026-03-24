"""
Local AI Service for ARC System - KenTrade Tender KTNA/OT/04/2025-2026

Data Sovereignty Compliant:
- Uses locally self-hosted Ollama LLM (no external API calls)
- Compliant with Kenya Data Protection Act 2019
- No data leaves the on-premise environment

Configuration in site_config.json:
    "ollama_base_url": "http://localhost:11434"   # Ollama server URL
    "ollama_model": "llama3"                       # Model to use (must be pulled in Ollama)
    "ollama_timeout": 120                          # Request timeout in seconds
"""

# pyright: reportMissingImports=false

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _safe_conf_get(key, default=None):
    try:
        import frappe
        conf = getattr(frappe, "conf", None)
        if conf:
            return conf.get(key, default)
    except Exception:
        pass
    return default


class LocalAIService:
    """
    Local AI service backed by Ollama for NLP, NLG, and text mining.

    This service is completely self-hosted and does not make any external
    network calls, ensuring compliance with the Kenya Data Protection Act 2019
    and data sovereignty requirements of the KenTrade tender.
    """

    def __init__(self, base_url: str = None, model: str = None, timeout: int = None):
        self.base_url = (
            base_url
            or _safe_conf_get("ollama_base_url", "http://localhost:11434")
        ).rstrip("/")
        self.model = model or _safe_conf_get("ollama_model", "llama3")
        self.timeout = int(timeout or _safe_conf_get("ollama_timeout", 120))

        # On-disk cache for deduplication
        cache_root = _safe_conf_get("ollama_cache_dir") or os.path.join(
            os.getcwd(), "ollama_cache"
        )
        os.makedirs(cache_root, exist_ok=True)
        self.cache_dir = cache_root
        self.cache_ttl = int(_safe_conf_get("ollama_cache_ttl", 86400))  # 1 day default

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def _cache_key(self, namespace: str, payload: str) -> str:
        h = hashlib.sha256()
        h.update((namespace + "|" + payload).encode("utf-8"))
        return h.hexdigest()

    def _cache_get(self, key: str) -> Optional[str]:
        path = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            if time.time() - data.get("ts", 0) > self.cache_ttl:
                os.remove(path)
                return None
            return data.get("value")
        except Exception:
            return None

    def _cache_set(self, key: str, value: str) -> None:
        path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(path, "w") as f:
                json.dump({"ts": time.time(), "value": value}, f)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------
    def _generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call the local Ollama /api/generate endpoint.
        Falls back gracefully if Ollama is unavailable.
        """
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except urllib.error.URLError as e:
            logger.warning("Ollama unavailable (%s); returning fallback.", e)
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error("Ollama error: %s", e)
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Rule-based fallback used when Ollama is offline during testing."""
        low = prompt.lower()
        if "risk" in low:
            return (
                "Risk identification requires manual review. "
                "Please ensure Ollama is running locally for AI-powered analysis."
            )
        if "summary" in low or "executive" in low:
            return (
                "Executive summary generation requires the local LLM. "
                "Please start Ollama and pull the configured model."
            )
        return "AI service unavailable. Please ensure Ollama is running locally."

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def identify_risks_from_text(self, document_text: str) -> Dict[str, Any]:
        """
        NLP-based risk identification from document text (text mining).
        Returns a structured list of identified risks with categories and severity hints.
        """
        if not document_text or not document_text.strip():
            return {"risks": [], "summary": "No text provided for analysis."}

        cache_key = self._cache_key("risk_id", document_text[:500])
        cached = self._cache_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        system = (
            "You are a senior Risk Officer specialising in ISO 31000 risk management "
            "and the Kenya Data Protection Act 2019. Analyse the provided text and "
            "identify risks. Return a JSON object with keys: "
            "'risks' (array of objects with: title, category, description, likelihood, impact, severity) "
            "and 'summary' (brief narrative). "
            "Risk categories: Strategic, Operational, Compliance, Financial, ICT, Reputational, Safety."
        )
        prompt = (
            f"Analyse the following document excerpt and identify all risks:\n\n"
            f"---\n{document_text[:3000]}\n---\n\n"
            "Return ONLY valid JSON."
        )

        raw = self._generate(prompt, system)

        # Attempt JSON parse; if LLM returned prose, wrap it
        try:
            result = json.loads(raw)
        except Exception:
            result = {"risks": [], "summary": raw}

        self._cache_set(cache_key, json.dumps(result))
        return result

    def generate_executive_summary(self, arc_metrics: Dict[str, Any]) -> str:
        """
        NLG: Generate a human-readable executive summary from ARC dashboard metrics.
        """
        metrics_str = json.dumps(arc_metrics, indent=2)
        cache_key = self._cache_key("exec_summary", metrics_str)
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        system = (
            "You are a Chief Risk Officer writing a concise executive summary for the "
            "Board of Directors. Use formal language. Keep to 150-200 words. "
            "Highlight critical risks, compliance gaps, and recommended priorities."
        )
        prompt = (
            "Based on the following ARC system metrics, write an executive summary:\n\n"
            f"{metrics_str}"
        )

        result = self._generate(prompt, system)
        self._cache_set(cache_key, result)
        return result

    def generate_risk_narrative(self, risk_data: Dict[str, Any]) -> str:
        """
        NLG: Generate a professional risk narrative for a given risk entry.
        """
        data_str = json.dumps(risk_data, indent=2)
        cache_key = self._cache_key("risk_narrative", data_str)
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        system = (
            "You are a Risk Officer. Write a formal 2-3 paragraph risk narrative "
            "suitable for a risk register report. Include: risk context, potential "
            "impact, recommended treatment strategy. Use ISO 31000 terminology."
        )
        prompt = f"Generate a risk narrative for the following risk data:\n\n{data_str}"

        result = self._generate(prompt, system)
        self._cache_set(cache_key, result)
        return result

    def generate_audit_finding_narrative(self, finding_data: Dict[str, Any]) -> str:
        """
        NLG: Generate a formal audit finding narrative for an audit engagement.
        """
        data_str = json.dumps(finding_data, indent=2)
        cache_key = self._cache_key("audit_finding", data_str)
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        system = (
            "You are a Senior Internal Auditor following GIAS standards. "
            "Write a formal audit finding narrative with: condition, criteria, "
            "cause, effect, and recommendation sections. Be concise and factual."
        )
        prompt = f"Generate an audit finding narrative for:\n\n{data_str}"

        result = self._generate(prompt, system)
        self._cache_set(cache_key, result)
        return result

    def classify_compliance_obligation(self, obligation_text: str) -> Dict[str, Any]:
        """
        NLP: Classify a compliance obligation text against known frameworks.
        Returns the most relevant framework, risk level, and key requirements.
        """
        cache_key = self._cache_key("compliance_classify", obligation_text[:300])
        cached = self._cache_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        system = (
            "You are a Compliance Officer specialising in Kenyan regulations. "
            "Classify the given text against these frameworks: "
            "ISO 31000, ISO 27001, Data Protection Act 2019, PFM Act, PSIAS, GIAS, COSO ERM. "
            "Return JSON with: framework, risk_level (Low/Medium/High/Critical), "
            "key_requirements (array), recommended_controls (array)."
        )
        prompt = (
            f"Classify this compliance obligation:\n\n{obligation_text[:2000]}\n\n"
            "Return ONLY valid JSON."
        )

        raw = self._generate(prompt, system)
        try:
            result = json.loads(raw)
        except Exception:
            result = {
                "framework": "Unknown",
                "risk_level": "Medium",
                "key_requirements": [],
                "recommended_controls": [],
                "raw_response": raw,
            }

        self._cache_set(cache_key, json.dumps(result))
        return result


# ------------------------------------------------------------------
# Frappe whitelisted API endpoints
# ------------------------------------------------------------------
def _get_service() -> LocalAIService:
    return LocalAIService()


def identify_risks_from_text(document_text: str) -> Dict[str, Any]:
    """Frappe-callable: identify risks from document text using local LLM."""
    try:
        import frappe
        frappe.only_for(["System Manager", "Risk Officer", "Auditor", "Incident Manager"])
    except Exception:
        pass
    return _get_service().identify_risks_from_text(document_text)


def generate_executive_summary(arc_metrics: Dict[str, Any]) -> str:
    """Frappe-callable: generate executive summary from ARC metrics."""
    return _get_service().generate_executive_summary(arc_metrics)


def generate_risk_narrative(risk_data: Dict[str, Any]) -> str:
    """Frappe-callable: generate risk narrative for a risk register entry."""
    return _get_service().generate_risk_narrative(risk_data)


def generate_audit_finding_narrative(finding_data: Dict[str, Any]) -> str:
    """Frappe-callable: generate audit finding narrative."""
    return _get_service().generate_audit_finding_narrative(finding_data)


def classify_compliance_obligation(obligation_text: str) -> Dict[str, Any]:
    """Frappe-callable: classify compliance obligation against frameworks."""
    return _get_service().classify_compliance_obligation(obligation_text)
