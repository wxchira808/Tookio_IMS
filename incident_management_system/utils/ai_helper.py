"""
AI Helper for Incident Management System

TOKEN CONSERVATION MODES:
To minimize API costs during testing, add to your site_config.json:

1. FALLBACK ONLY (No API calls):
   "ai_testing_mode": "fallback_only"

2. LIMITED TOKENS (150 tokens max):
   "ai_testing_mode": "limited"

3. FULL AI (800 tokens max, with caching):
   "ai_testing_mode": "full"  # or omit this setting

Other cost controls:
- "openai_max_tokens": 500  # Global token limit
- "openai_cache_ttl": 604800  # Cache for 7 days (default)
- "openai_model": "gpt-3.5-turbo"  # Cheapest model (default)
"""

import frappe
import openai
import json
import os
import hashlib
import time
from frappe import _


class AIReportGenerator:
    """AI-powered report generation for Incident Management System"""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize OpenAI client.

        Accept optional api_key and model so the helper can be used outside a running
        Frappe context (e.g., during import/unit tests). Falls back to `frappe.conf` when
        available.
        """
        # prefer explicit args, then site config. Use a safe accessor in case frappe isn't bound
        def _safe_conf_get(key):
            try:
                conf = getattr(frappe, 'conf', None)
                if conf:
                    return conf.get(key)
            except Exception:
                pass
            return None

        api_key = api_key or _safe_conf_get('openai_api_key')
        self.model = model or _safe_conf_get('openai_model') or 'gpt-3.5-turbo'

        if not api_key:
            # avoid raising when used in non-Frappe contexts during static checks; raise meaningful error at call-time
            raise RuntimeError("OpenAI API key not configured. Please add 'openai_api_key' to site_config.json or pass api_key to AIReportGenerator.")

        self.client = openai.OpenAI(api_key=api_key)

        # caching and cost-control settings (can be set in site_config.json)
        self.cache_dir = _safe_conf_get('openai_cache_dir') or os.path.join(os.getcwd(), 'openai_cache')
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            # best-effort, fallback to /tmp
            self.cache_dir = '/tmp/incident_ai_cache'
            os.makedirs(self.cache_dir, exist_ok=True)

        # TTL in seconds, default 7 days
        self.cache_ttl = int(_safe_conf_get('openai_cache_ttl') or 7 * 24 * 60 * 60)
        # global max tokens cap to avoid big bills (default 800)
        self.max_tokens_cap = int(_safe_conf_get('openai_max_tokens') or 800)

    # --- simple on-disk cache helpers ---
    def _cache_key(self, namespace, payload: str):
        h = hashlib.sha256()
        h.update((namespace + '|' + payload).encode('utf-8'))
        return h.hexdigest()

    def _cache_get(self, key):
        path = os.path.join(self.cache_dir, key + '.json')
        try:
            if not os.path.exists(path):
                return None
            st = os.stat(path)
            if time.time() - st.st_mtime > self.cache_ttl:
                return None
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _cache_set(self, key, value):
        path = os.path.join(self.cache_dir, key + '.json')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(value, f)
        except Exception:
            pass

    def generate_incident_summary(self, incident_name):
        """Generate AI-powered incident summary report"""
        try:
            incident = frappe.get_doc("Incident", incident_name)
            prompt = self._build_incident_summary_prompt(incident)

            # cost-control: conservative max tokens for summaries
            max_tokens = min(400, self.max_tokens_cap)
            cache_payload = json.dumps({'model': self.model, 'prompt': prompt, 'max_tokens': max_tokens})
            key = self._cache_key('incident_summary', cache_payload)
            cached = self._cache_get(key)
            if cached:
                return cached.get('result')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert incident management analyst. Generate professional, concise incident summary reports."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )

            result = response.choices[0].message.content
            
            # Extract token usage information
            tokens_used = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            
            # Cache the result with metadata
            cache_data = {
                'result': result, 
                'ts': int(time.time()),
                'tokens_used': tokens_used,
                'model': self.model
            }
            self._cache_set(key, cache_data)
            
            return {
                'content': result,
                'tokens_used': tokens_used,
                'model': self.model
            }

        except openai.RateLimitError:
            # Demo fallback when quota exceeded
            demo_result = self._get_demo_summary(incident_name)
            return {
                'content': demo_result,
                'tokens_used': 0,
                'model': 'demo-fallback'
            }
        except Exception as e:
            frappe.log_error(f"AI Report Generation Error: {str(e)}")
            return f"Error generating AI summary: {str(e)}"

    def _get_demo_summary(self, incident_name):
        """Concise placeholder used when AI is unavailable or quota is exceeded.

        This placeholder does not claim to be an AI-generated report.
        """
        return f"[DEMO] AI unavailable — summary not generated for incident {incident_name}."

    def generate_investigation_report(self, investigation_name):
        """Generate AI-powered investigation analysis"""
        try:
            investigation = frappe.get_doc("Incident Investigation", investigation_name)
            incident = frappe.get_doc("Incident", investigation.incident)

            prompt = self._build_investigation_prompt(investigation, incident)

            # investigation reports can be longer but cap to control cost
            max_tokens = min(800, self.max_tokens_cap)
            cache_payload = json.dumps({'model': self.model, 'prompt': prompt, 'max_tokens': max_tokens})
            key = self._cache_key('investigation_report', cache_payload)
            cached = self._cache_get(key)
            if cached:
                return cached.get('result')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional incident investigator. Analyze evidence and provide detailed investigation reports with actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )

            result = response.choices[0].message.content
            self._cache_set(key, {'result': result, 'ts': int(time.time())})
            return result

        except Exception as e:
            frappe.log_error(f"AI Investigation Report Error: {str(e)}")
            return f"Error generating AI investigation report: {str(e)}"

    def suggest_investigation_steps(self, incident_type, severity, description):
        """AI-powered investigation step suggestions"""
        try:
            prompt = f"""
            Incident Type: {incident_type}
            Severity: {severity}
            Description: {description}

            Based on this incident information, suggest 5-7 specific investigation steps that should be taken. 
            Format as a numbered list with brief explanations for each step.
            """

            max_tokens = min(200, self.max_tokens_cap)
            cache_payload = json.dumps({'model': self.model, 'prompt': prompt, 'max_tokens': max_tokens})
            key = self._cache_key('investigation_steps', cache_payload)
            cached = self._cache_get(key)
            if cached:
                return cached.get('result')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an incident investigation expert. Provide practical, actionable investigation steps."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.4
            )

            result = response.choices[0].message.content
            self._cache_set(key, {'result': result, 'ts': int(time.time())})
            return result

        except openai.RateLimitError:
            return self._get_demo_investigation_steps(incident_type, severity)
        except Exception as e:
            frappe.log_error(f"AI Investigation Steps Error: {str(e)}")
            return f"Error generating investigation suggestions: {str(e)}"

    def _get_demo_investigation_steps(self, incident_type, severity):
        """Placeholder investigation steps used when AI is unavailable.

        This is not a real AI-generated recommendation. Configure OpenAI credentials or retry later to get live guidance.
        """
        return (
            f"[DEMO] AI unavailable: no investigation steps generated for type '{incident_type}' (severity: {severity}). "
            "Suggested immediate actions: secure scene; document evidence; notify investigators."
        )

    def analyze_incident_trends(self, incidents_data):
        """Analyze trends across multiple incidents"""
        try:
            prompt = self._build_trend_analysis_prompt(incidents_data)

            max_tokens = min(600, self.max_tokens_cap)
            cache_payload = json.dumps({'model': self.model, 'prompt': prompt, 'max_tokens': max_tokens})
            key = self._cache_key('trend_analysis', cache_payload)
            cached = self._cache_get(key)
            if cached:
                return cached.get('result')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst specializing in incident management trends. Identify patterns, risks, and improvement opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )

            result = response.choices[0].message.content
            self._cache_set(key, {'result': result, 'ts': int(time.time())})
            return result

        except Exception as e:
            frappe.log_error(f"AI Trend Analysis Error: {str(e)}")
            return f"Error generating trend analysis: {str(e)}"

    def _build_incident_summary_prompt(self, incident):
        """Build structured prompt for incident summary"""
        return f"""
        Please generate a professional incident summary report for the following incident:

        INCIDENT DETAILS:
        - ID: {incident.name}
        - Title: {incident.get('title1', 'N/A')}
        - Type: {incident.get('incident_type', 'N/A')}
        - Severity: {incident.get('severity', 'N/A')}
        - Status: {incident.get('status', 'N/A')}
        - Date: {incident.get('incident_date', 'N/A')}
        - Location: {incident.get('location', 'N/A')}
        - Description: {incident.get('description', 'N/A')}
        - Immediate Actions: {incident.get('immediate_action_taken', 'N/A')}
        - Injuries: {incident.get('injuries_involved', 'N/A')}
        - Property Damage: {incident.get('property_damage', 'N/A')}
        - Impact: {incident.get('business_impact_description', 'N/A')}

        Please provide:
        1. Executive Summary (2-3 sentences)
        2. Key Impact Points
        3. Current Status
        4. Next Steps/Recommendations
        5. Risk Assessment

        Format as a professional business report.
        """

    def _build_investigation_prompt(self, investigation, incident):
        """Build structured prompt for investigation analysis"""
        return f"""
        Please analyze this incident investigation and provide a comprehensive report:

        INCIDENT CONTEXT:
        - Incident ID: {incident.name}
        - Type: {incident.get('incident_type', 'N/A')}
        - Severity: {incident.get('severity', 'N/A')}
        - Description: {incident.get('description', 'N/A')}

        INVESTIGATION DETAILS:
        - Investigation ID: {investigation.name}
        - Type: {investigation.get('investigation_type', 'N/A')}
        - Priority: {investigation.get('investigation_priority', 'N/A')}
        - Status: {investigation.get('investigation_status', 'N/A')}
        - Method: {investigation.get('investigation_method', 'N/A')}
        - Scope: {investigation.get('investigation_scope', 'N/A')}
        - Objectives: {investigation.get('investigation_objective', 'N/A')}
        - Evidence: {investigation.get('evidence_collected', 'N/A')}
        - Witnesses: {investigation.get('key_witnesses', 'N/A')}
        - Findings: {investigation.get('investigation_findings', 'N/A')}
        - Root Cause: {investigation.get('root_cause_analysis', 'N/A')}
        - Contributing Factors: {investigation.get('contributing_factors_identified', 'N/A')}

        Please provide:
        1. Investigation Summary
        2. Evidence Analysis
        3. Root Cause Assessment
        4. Contributing Factors Analysis
        5. Recommendations for Prevention
        6. Lessons Learned
        7. Follow-up Actions Required

        Format as a professional investigation report.
        """

    def _build_trend_analysis_prompt(self, incidents_data):
        """Build prompt for trend analysis across incidents"""
        incidents_summary = []
        for incident in incidents_data:
            incidents_summary.append({
                'id': incident.get('name'),
                'type': incident.get('incident_type'),
                'severity': incident.get('severity'),
                'date': str(incident.get('incident_date')),
                'location': incident.get('location'),
                'status': incident.get('status')
            })

        return f"""
        Analyze the following incident data for trends and patterns:

        INCIDENT DATA:
        {json.dumps(incidents_summary, indent=2)}

        Please identify:
        1. Incident Type Patterns
        2. Severity Trends
        3. Geographic Patterns (if locations provided)
        4. Temporal Patterns
        5. Risk Areas
        6. Improvement Opportunities
        7. Preventive Recommendations

        Provide actionable insights for incident management improvement.
        """

# Utility functions for easy access
def generate_ai_incident_summary(incident_name):
    """Public function to generate AI incident summary"""
    generator = AIReportGenerator()
    result = generator.generate_incident_summary(incident_name)
    
    # Return content for backward compatibility, but log metadata
    if isinstance(result, dict):
        return result.get('content', result)
    return result


def generate_ai_investigation_report(investigation_name):
    """Public function to generate AI investigation report"""
    generator = AIReportGenerator()
    return generator.generate_investigation_report(investigation_name)


def get_ai_investigation_suggestions(incident_type, severity, description):
    """Public function to get AI investigation suggestions"""
    generator = AIReportGenerator()
    return generator.suggest_investigation_steps(incident_type, severity, description)


def analyze_incident_trends_ai(date_range=30):
    """Public function to analyze incident trends using AI"""
    from frappe.utils import add_days, today

    start_date = add_days(today(), -date_range)
    incidents = frappe.get_all("Incident", 
        filters={"incident_date": [">=", start_date]},
        fields=["name", "incident_type", "severity", "incident_date", "location", "status"]
    )

    generator = AIReportGenerator()
    return generator.analyze_incident_trends(incidents)


@frappe.whitelist()
def get_incident_assistance(incident_name, user_question, incident_data, conversation_history=None):
    """
    AI Assistant for incident management - provides conversational help and guidance
    """
    
    # Parse JSON strings if they come as strings
    if isinstance(incident_data, str):
        incident_data = json.loads(incident_data)
    if isinstance(conversation_history, str):
        conversation_history = json.loads(conversation_history)
    
    # FOR TESTING: Check if we should use AI or just fallback responses
    # You can set 'ai_testing_mode' to 'fallback_only' in site_config.json to avoid any API calls during testing
    try:
        testing_mode = frappe.conf.get('ai_testing_mode', 'full')  # 'full', 'fallback_only', 'limited'
        
        if testing_mode == 'fallback_only':
            # Skip AI entirely during testing - use only pre-configured responses
            raise Exception("Testing mode: using fallback responses only")
            
        elif testing_mode == 'limited':
            # Use very conservative token limits during testing
            max_tokens_override = 150  # Very small for testing
        else:
            max_tokens_override = None
            
        generator = AIReportGenerator()
        
        # Override max tokens for testing if specified
        if max_tokens_override:
            generator.max_tokens = min(generator.max_tokens, max_tokens_override)
        
        # Get additional context from related records
        investigation = frappe.db.get_value("Incident Investigation", 
            {"incident": incident_name}, 
            ["name", "investigation_status", "preliminary_assessment", "investigation_findings"])
        
        resolution = frappe.db.get_value("Incident Resolution", 
            {"incident": incident_name}, 
            ["name", "resolution_status", "resolution_summary"])
        
        # Build context for AI
        context_prompt = f"""
You are an AI assistant helping with incident management. You're an expert in incident response, investigation, and resolution.

CURRENT INCIDENT DETAILS:
- Title: {incident_data.get('title', 'N/A')}
- Description: {incident_data.get('description', 'N/A')}
- Severity: {incident_data.get('severity', 'N/A')}
- Priority: {incident_data.get('priority', 'N/A')}  
- Status: {incident_data.get('status', 'N/A')}
- Type: {incident_data.get('incident_type', 'N/A')}
- Reported Date: {incident_data.get('reported_date', 'N/A')}

RELATED RECORDS:
- Investigation: {'Yes' if investigation else 'No'}
{f"  - Status: {investigation[1] if investigation else 'N/A'}" if investigation else ""}
- Resolution: {'Yes' if resolution else 'No'}
{f"  - Status: {resolution[1] if resolution else 'N/A'}" if resolution else ""}

CONVERSATION HISTORY:
{json.dumps(conversation_history or [], indent=2)}

USER QUESTION: {user_question}

Please provide helpful, actionable advice specific to this incident. Be concise but comprehensive. 
Focus on practical next steps, best practices, and relevant considerations.
If the user asks about specific processes, provide step-by-step guidance.
"""

        # Generate AI response
        response = generator.client.chat.completions.create(
            model=generator.model,
            messages=[
                {"role": "system", "content": "You are an expert incident management assistant. Provide clear, actionable guidance."},
                {"role": "user", "content": context_prompt}
            ],
            max_tokens=generator.max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        frappe.log_error(f"AI Assistance Error: {str(e)}")
        
        # Parse JSON strings for fallback responses
        try:
            if isinstance(incident_data, str):
                incident_data = json.loads(incident_data)
        except:
            incident_data = {}
        
        # Provide fallback response based on question keywords
        question_lower = user_question.lower()
        
        if any(word in question_lower for word in ['next', 'step', 'what should', 'how to']):
            return f"Based on your incident's {incident_data.get('severity', 'unknown')} severity and {incident_data.get('status', 'unknown')} status, here are some general next steps:\n\n1. Ensure proper documentation of the incident\n2. Assess impact and assign appropriate priority\n3. Consider creating an investigation if not already done\n4. Keep stakeholders informed of progress\n5. Follow your organization's incident response procedures"
            
        elif any(word in question_lower for word in ['similar', 'past', 'history']):
            return "To find similar incidents, you can:\n\n1. Search incidents by type or keywords\n2. Review incidents with similar severity levels\n3. Check the incident dashboard for patterns\n4. Consult with team members who have handled similar cases"
            
        elif any(word in question_lower for word in ['priority', 'urgent', 'critical']):
            return f"For a {incident_data.get('severity', 'unknown')} severity incident:\n\n1. Follow your organization's priority matrix\n2. Consider business impact and urgency\n3. Ensure appropriate resources are allocated\n4. Set realistic timelines for resolution\n5. Communicate priority level to all stakeholders"
            
        else:
            return "I'm here to help with your incident management. You can ask me about:\n\n• Next steps for this incident\n• Best practices for incident handling\n• How to prioritize and escalate\n• Investigation and resolution guidance\n• Similar incidents or patterns\n\nPlease try rephrasing your question, and I'll do my best to help!"
