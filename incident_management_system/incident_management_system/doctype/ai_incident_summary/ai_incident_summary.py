# Copyright (c) 2025, Brian and contributors
# For license information, please see license.txt

import frappe
import json
import re
from frappe.model.document import Document

class AIIncidentSummary(Document):
    def validate(self):
        """Validate the AI summary before saving"""
        if not self.title:
            self.title = f"AI Summary for {self.incident}"
        
        # Extract data from raw response if not already done
        if self.raw_ai_response and not self.extracted_data:
            self.extract_structured_data()
    
    def extract_structured_data(self):
        """Extract structured data from raw AI response"""
        if not self.raw_ai_response:
            return
        
        extracted = {}
        content = self.raw_ai_response
        
        try:
            # More flexible patterns to match various AI response formats
            
            # Extract Executive Summary - multiple patterns
            exec_patterns = [
                r'(?:Executive Summary|EXECUTIVE SUMMARY)[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)',
                r'(?:Summary|SUMMARY)[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)',
                r'\*\*Executive Summary\*\*[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)'
            ]
            for pattern in exec_patterns:
                exec_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if exec_match:
                    self.executive_summary = exec_match.group(1).strip()
                    extracted['executive_summary'] = self.executive_summary
                    break
            
            # Extract Key Findings/Impact Points - more flexible
            findings_patterns = [
                r'(?:Key Impact Points|Key Findings|KEY FINDINGS|Impact Points)[:\s]*\n((?:[\*\-•]\s*[^\n]+(?:\n(?!\w+:))*)+)',
                r'(?:Impact Assessment|IMPACT ASSESSMENT)[:\s]*\n((?:[\*\-•]\s*[^\n]+(?:\n(?!\w+:))*)+)',
                r'\*\*Key.*?Points?\*\*[:\s]*\n((?:[\*\-•]\s*[^\n]+(?:\n(?!\w+:))*)+)',
                r'(?:Findings|FINDINGS)[:\s]*\n((?:[\*\-•]\s*[^\n]+(?:\n(?!\w+:))*)+)'
            ]
            for pattern in findings_patterns:
                findings_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if findings_match:
                    self.key_findings = findings_match.group(1).strip()
                    extracted['key_findings'] = self.key_findings
                    break
            
            # Extract Recommendations - more patterns
            rec_patterns = [
                r'(?:Next Steps|Recommendations|RECOMMENDATIONS|Immediate Recommendations)[:\s]*\n((?:[\*\-•\d]+[\.\)]\s*[^\n]+(?:\n(?!\w+:))*)+)',
                r'\*\*(?:Next Steps|Recommendations)\*\*[:\s]*\n((?:[\*\-•\d]+[\.\)]\s*[^\n]+(?:\n(?!\w+:))*)+)',
                r'(?:Actions|ACTIONS)[:\s]*\n((?:[\*\-•\d]+[\.\)]\s*[^\n]+(?:\n(?!\w+:))*)+)'
            ]
            for pattern in rec_patterns:
                rec_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if rec_match:
                    self.recommendations = rec_match.group(1).strip()
                    extracted['recommendations'] = self.recommendations
                    break
            
            # Extract Risk Assessment - more flexible
            risk_patterns = [
                r'(?:Risk Assessment|RISK ASSESSMENT)[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)',
                r'\*\*Risk Assessment\*\*[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)',
                r'(?:Risk|RISK)[:\s]*\n([^#\n]*(?:\n(?![\*#\-\d\w]+:)[^\n]*)*)'
            ]
            for pattern in risk_patterns:
                risk_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if risk_match:
                    self.risk_assessment = risk_match.group(1).strip()
                    extracted['risk_assessment'] = self.risk_assessment
                    break
            
            # Fallback: try to extract any numbered or bulleted sections
            if not any([self.executive_summary, self.key_findings, self.recommendations, self.risk_assessment]):
                # Split content into sections and try to categorize
                sections = re.split(r'\n\s*\n', content)
                for section in sections:
                    section = section.strip()
                    if not section:
                        continue
                        
                    # Look for executive/summary-like content in first sections
                    if not self.executive_summary and len(section) > 50 and not re.match(r'[\*\-•\d]', section):
                        if any(word in section.lower() for word in ['summary', 'executive', 'overview', 'incident']):
                            self.executive_summary = section[:500]  # Limit length
                            extracted['executive_summary'] = self.executive_summary
                    
                    # Look for bulleted/numbered content
                    if re.search(r'[\*\-•]\s*', section) or re.search(r'\d+\.\s*', section):
                        if not self.key_findings and any(word in section.lower() for word in ['finding', 'impact', 'injury', 'damage']):
                            self.key_findings = section
                            extracted['key_findings'] = self.key_findings
                        elif not self.recommendations and any(word in section.lower() for word in ['recommend', 'action', 'step', 'next']):
                            self.recommendations = section
                            extracted['recommendations'] = self.recommendations
            
            # Store extracted data as JSON
            self.extracted_data = json.dumps(extracted, indent=2)
            
            # Create formatted HTML summary
            self.create_formatted_summary()
            
            # Log extraction for debugging
            frappe.log_error(f"AI Summary Extraction Debug - Incident: {self.incident}, "
                           f"Executive: {bool(self.executive_summary)}, "
                           f"Findings: {bool(self.key_findings)}, "
                           f"Recommendations: {bool(self.recommendations)}, "
                           f"Risk: {bool(self.risk_assessment)}")
            
        except Exception as e:
            frappe.log_error(f"Error extracting data from AI summary: {str(e)}\nContent preview: {content[:500]}")
            # Fallback: store raw content as executive summary
            if content and not self.executive_summary:
                self.executive_summary = content[:1000]
    
    def create_formatted_summary(self):
        """Create a nicely formatted HTML summary for display"""
        if not self.raw_ai_response:
            return
        
        html_parts = []
        
        if self.executive_summary:
            html_parts.append(f"""
            <div class="ai-summary-section">
                <h4>Executive Summary</h4>
                <p>{self.executive_summary}</p>
            </div>
            """)
        
        if self.key_findings:
            findings_html = self.key_findings.replace('•', '&bull;').replace('- ', '&bull; ')
            html_parts.append(f"""
            <div class="ai-summary-section">
                <h4>Key Findings</h4>
                <div class="findings-list">{findings_html}</div>
            </div>
            """)
        
        if self.recommendations:
            rec_html = self.recommendations.replace('•', '&bull;').replace('- ', '&bull; ')
            html_parts.append(f"""
            <div class="ai-summary-section">
                <h4>Recommendations</h4>
                <div class="recommendations-list">{rec_html}</div>
            </div>
            """)
        
        if self.risk_assessment:
            html_parts.append(f"""
            <div class="ai-summary-section">
                <h4>Risk Assessment</h4>
                <p>{self.risk_assessment}</p>
            </div>
            """)
        
        if html_parts:
            self.summary_content = f"""
            <div class="ai-incident-summary">
                <style>
                .ai-summary-section {{ margin-bottom: 20px; }}
                .ai-summary-section h4 {{ color: #2490ef; margin-bottom: 8px; }}
                .findings-list, .recommendations-list {{ margin-left: 15px; }}
                </style>
                {''.join(html_parts)}
            </div>
            """

@frappe.whitelist()
def get_incident_ai_summary(incident_name):
    """Get existing AI summary for an incident or create new one"""
    # Check if summary already exists
    existing = frappe.get_all("AI Incident Summary", 
        filters={"incident": incident_name},
        fields=["name", "title", "summary_content", "generated_on"],
        order_by="generated_on desc",
        limit=1
    )
    
    if existing:
        return {
            "exists": True,
            "summary": existing[0],
            "message": "Using existing AI summary"
        }
    
    return {
        "exists": False,
        "message": "No existing summary found"
    }

@frappe.whitelist()
def create_ai_summary(incident_name, ai_response, model_used="gpt-3.5-turbo", tokens_used=0, generation_time=0):
    """Create and save a new AI incident summary"""
    try:
        # Create new AI Summary document
        ai_summary = frappe.new_doc("AI Incident Summary")
        ai_summary.incident = incident_name
        ai_summary.raw_ai_response = ai_response
        ai_summary.model_used = model_used
        ai_summary.tokens_used = tokens_used
        ai_summary.generation_time = generation_time
        
        # This will trigger extract_structured_data in validate()
        ai_summary.save()
        
        return {
            "success": True,
            "name": ai_summary.name,
            "title": ai_summary.title,
            "summary_content": ai_summary.summary_content,
            "message": "AI summary created and saved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating AI summary: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create AI summary"
        }
