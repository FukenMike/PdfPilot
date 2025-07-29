import json
from datetime import datetime
from typing import Dict, List, Any
from io import BytesIO
import os
from openai import OpenAI

class ReportGenerator:
    """Generate comprehensive legal analysis reports and summaries"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
    
    def generate_case_summary(self, case_data: Dict[str, Any], development_mode: bool = False) -> str:
        """Generate comprehensive case summary report"""
        
        case_name = case_data.get('case_name', 'Unknown Case')
        documents = case_data.get('documents', {})
        violations = case_data.get('violations', [])
        timeline = case_data.get('timeline', [])
        entities = case_data.get('entities', {})
        actor_tracking = case_data.get('actor_tracking', {})
        
        # Basic case statistics
        total_docs = len(documents)
        total_violations = len(violations)
        high_severity = len([v for v in violations if v.get('severity') == 'high'])
        medium_severity = len([v for v in violations if v.get('severity') == 'medium'])
        low_severity = len([v for v in violations if v.get('severity') == 'low'])
        
        # Generate report sections
        report = f"""
# LEGAL CASE ANALYSIS REPORT
## Case: {case_name}
### Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

---

## EXECUTIVE SUMMARY

**Total Documents Analyzed:** {total_docs}
**Total Violations Identified:** {total_violations}
- High Severity: {high_severity}
- Medium Severity: {medium_severity}  
- Low Severity: {low_severity}

**Risk Assessment:** {self._calculate_risk_level(violations)}

---

## DOCUMENT INVENTORY
"""
        
        # Document list
        for i, (doc_hash, doc_info) in enumerate(documents.items(), 1):
            filename = doc_info.get('filename', 'Unknown Document')
            doc_type = doc_info.get('legal_analysis', {}).get('document_type', {}).get('type', 'unknown')
            upload_date = doc_info.get('upload_date', 'Unknown')
            
            report += f"{i}. **{filename}**\n   - Type: {doc_type.title()}\n   - Processed: {upload_date[:10] if upload_date != 'Unknown' else 'Unknown'}\n\n"
        
        # Legal entities section
        report += "\n---\n\n## KEY LEGAL ENTITIES\n\n"
        
        if entities.get('case_numbers'):
            report += f"**Case Numbers:** {', '.join(list(entities['case_numbers'])[:5])}\n\n"
        if entities.get('judges'):
            report += f"**Judges:** {', '.join(list(entities['judges'])[:5])}\n\n"
        if entities.get('attorneys'):
            report += f"**Attorneys:** {', '.join(list(entities['attorneys'])[:5])}\n\n"
        if entities.get('courts'):
            report += f"**Courts:** {', '.join(list(entities['courts'])[:3])}\n\n"
        
        # Violations section
        report += "\n---\n\n## VIOLATIONS AND ISSUES IDENTIFIED\n\n"
        
        if violations:
            # Group violations by severity
            high_violations = [v for v in violations if v.get('severity') == 'high']
            medium_violations = [v for v in violations if v.get('severity') == 'medium']
            low_violations = [v for v in violations if v.get('severity') == 'low']
            
            if high_violations:
                report += "### 🚨 HIGH SEVERITY VIOLATIONS\n\n"
                for i, violation in enumerate(high_violations[:10], 1):
                    report += f"{i}. **{violation.get('description', violation.get('type', 'Unknown')).title()}**\n"
                    report += f"   - Document: {violation.get('document_name', 'Unknown')}\n"
                    report += f"   - Context: {violation.get('context', 'No context available')[:150]}...\n\n"
            
            if medium_violations:
                report += "### ⚠️ MEDIUM SEVERITY VIOLATIONS\n\n"
                for i, violation in enumerate(medium_violations[:10], 1):
                    report += f"{i}. **{violation.get('description', violation.get('type', 'Unknown')).title()}**\n"
                    report += f"   - Document: {violation.get('document_name', 'Unknown')}\n"
                    report += f"   - Context: {violation.get('context', 'No context available')[:150]}...\n\n"
        else:
            report += "No violations detected in the analyzed documents.\n\n"
        
        # Timeline section
        if timeline:
            report += "\n---\n\n## CASE TIMELINE\n\n"
            for event in timeline[:20]:  # Show first 20 events
                date_str = event.get('date_str', 'Unknown Date')
                doc_name = event.get('document', 'Unknown Document')
                doc_type = event.get('document_type', 'unknown')
                report += f"- **{date_str}** - {doc_type.title()} ({doc_name})\n"
        
        # Actor tracking section
        if actor_tracking:
            report += "\n---\n\n## REPEAT ACTORS WITH VIOLATIONS\n\n"
            sorted_actors = sorted(actor_tracking.items(), 
                                 key=lambda x: x[1].get('severity_score', 0), reverse=True)
            
            for actor, info in sorted_actors[:10]:
                actor_type = info.get('type', 'unknown').title()
                violation_count = len(info.get('violations', []))
                severity_score = info.get('severity_score', 0)
                documents = info.get('documents', [])
                
                report += f"**{actor}** ({actor_type})\n"
                report += f"- Violations: {violation_count}\n"
                report += f"- Severity Score: {severity_score}\n"
                report += f"- Documents: {', '.join(documents[:3])}\n\n"
        
        # AI Analysis section
        if not development_mode:
            ai_analysis = self._generate_ai_analysis(case_data)
            report += f"\n---\n\n## AI LEGAL ANALYSIS\n\n{ai_analysis}\n"
        else:
            report += "\n---\n\n## AI LEGAL ANALYSIS\n\n[Development Mode Active - AI analysis disabled to save tokens]\n"
        
        # Recommendations section
        report += "\n---\n\n## RECOMMENDATIONS\n\n"
        recommendations = self._generate_recommendations(violations, actor_tracking)
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"\n---\n\n*Report generated by Legal Document Analysis System on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
        
        return report
    
    def generate_violation_briefing(self, violations: List[Dict[str, Any]], case_name: str = "Unknown Case") -> str:
        """Generate focused briefing on violations for legal action"""
        
        briefing = f"""
# VIOLATION BRIEFING
## Case: {case_name}
### Date: {datetime.now().strftime('%B %d, %Y')}

---

## SUMMARY OF LEGAL VIOLATIONS

"""
        
        # Group by severity
        high_violations = [v for v in violations if v.get('severity') == 'high']
        medium_violations = [v for v in violations if v.get('severity') == 'medium']
        low_violations = [v for v in violations if v.get('severity') == 'low']
        
        briefing += f"**Total Violations:** {len(violations)}\n"
        briefing += f"- Critical/High: {len(high_violations)}\n"
        briefing += f"- Medium: {len(medium_violations)}\n"
        briefing += f"- Low: {len(low_violations)}\n\n"
        
        # Detailed violation analysis
        if high_violations:
            briefing += "## CRITICAL VIOLATIONS REQUIRING IMMEDIATE ATTENTION\n\n"
            for i, violation in enumerate(high_violations, 1):
                briefing += f"### {i}. {violation.get('description', 'Unknown Violation').upper()}\n\n"
                briefing += f"**Document:** {violation.get('document_name', 'Unknown')}\n\n"
                briefing += f"**Evidence:** {violation.get('context', 'No context available')}\n\n"
                briefing += f"**Legal Significance:** This represents a {violation.get('severity', 'unknown')} severity violation that may constitute grounds for legal challenge.\n\n"
                briefing += "---\n\n"
        
        if medium_violations:
            briefing += "## SIGNIFICANT PROCEDURAL VIOLATIONS\n\n"
            for i, violation in enumerate(medium_violations[:5], 1):  # Limit to top 5
                briefing += f"### {i}. {violation.get('description', 'Unknown Violation').title()}\n\n"
                briefing += f"**Document:** {violation.get('document_name', 'Unknown')}\n\n"
                briefing += f"**Context:** {violation.get('context', 'No context available')[:200]}...\n\n"
                briefing += "---\n\n"
        
        return briefing
    
    def generate_legal_brief_template(self, case_data: Dict[str, Any], development_mode: bool = False) -> str:
        """Generate template for legal brief based on identified violations"""
        
        if development_mode:
            return """
# LEGAL BRIEF TEMPLATE

[Development Mode Active - Legal brief generation disabled to save tokens]

Enable production mode to generate AI-powered legal brief templates based on your case violations and evidence.
"""
        
        try:
            violations = case_data.get('violations', [])
            entities = case_data.get('entities', {})
            case_name = case_data.get('case_name', 'Unknown Case')
            
            # Prepare violation summary for AI
            violation_summary = []
            for v in violations[:10]:  # Top 10 violations
                violation_summary.append({
                    'type': v.get('type', 'unknown'),
                    'severity': v.get('severity', 'low'),
                    'description': v.get('description', ''),
                    'document': v.get('document_name', 'Unknown')
                })
            
            prompt = f"""
            Create a legal brief template for a family court/child welfare case with the following details:
            
            Case Name: {case_name}
            Violations Found: {json.dumps(violation_summary, indent=2)}
            Key Entities: {dict(list(entities.items())[:5]) if entities else {}}
            
            Generate a professional legal brief template with:
            1. Caption/Header
            2. Introduction/Statement of the Case
            3. Statement of Facts
            4. Argument sections based on violations
            5. Prayer for Relief
            6. Conclusion
            
            Focus on constitutional violations, due process issues, and procedural failures commonly found in family court cases.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an experienced family law attorney creating legal brief templates. Focus on constitutional and procedural violations in child welfare cases."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"""
# LEGAL BRIEF TEMPLATE - ERROR

An error occurred while generating the legal brief template: {str(e)}

Please check your API configuration and try again.
"""
    
    def export_case_data(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export case data in structured format for external use"""
        
        export_data = {
            'case_info': {
                'case_id': case_data.get('case_id', ''),
                'case_name': case_data.get('case_name', ''),
                'created_date': case_data.get('created_date', ''),
                'last_updated': case_data.get('last_updated', ''),
                'export_date': datetime.now().isoformat()
            },
            'documents': [],
            'violations': case_data.get('violations', []),
            'timeline': case_data.get('timeline', []),
            'entities': {k: list(v) if isinstance(v, set) else v for k, v in case_data.get('entities', {}).items()},
            'actor_tracking': case_data.get('actor_tracking', {}),
            'statistics': {
                'total_documents': len(case_data.get('documents', {})),
                'total_violations': len(case_data.get('violations', [])),
                'severity_breakdown': self._get_severity_breakdown(case_data.get('violations', [])),
                'risk_level': self._calculate_risk_level(case_data.get('violations', []))
            }
        }
        
        # Simplified document info for export
        for doc_hash, doc_info in case_data.get('documents', {}).items():
            export_data['documents'].append({
                'hash': doc_hash,
                'filename': doc_info.get('filename', 'Unknown'),
                'upload_date': doc_info.get('upload_date', ''),
                'document_type': doc_info.get('legal_analysis', {}).get('document_type', {}).get('type', 'unknown'),
                'violation_count': len([v for v in case_data.get('violations', []) if v.get('document_hash') == doc_hash])
            })
        
        return export_data
    
    def _generate_ai_analysis(self, case_data: Dict[str, Any]) -> str:
        """Generate AI-powered legal analysis"""
        try:
            violations = case_data.get('violations', [])
            entities = case_data.get('entities', {})
            
            # Prepare summary for AI
            violation_types = list(set(v.get('type', 'unknown') for v in violations))
            high_severity_count = len([v for v in violations if v.get('severity') == 'high'])
            
            prompt = f"""
            Provide a professional legal analysis of this family court/child welfare case based on the following information:
            
            Violation Types Found: {violation_types[:10]}
            High Severity Violations: {high_severity_count}
            Total Violations: {len(violations)}
            Key Entities: {dict(list(entities.items())[:5]) if entities else {}}
            
            Focus on:
            1. Overall case assessment
            2. Most concerning legal issues
            3. Constitutional/due process implications
            4. Strategic considerations
            5. Recommended next steps
            
            Provide analysis in 2-3 paragraphs suitable for legal professionals.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an experienced family law attorney providing case analysis. Focus on constitutional issues and procedural violations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]], actor_tracking: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []
        
        high_violations = [v for v in violations if v.get('severity') == 'high']
        
        if high_violations:
            recommendations.append("Immediately consult with a qualified family law attorney regarding the constitutional violations identified")
            recommendations.append("Document all high-severity violations with supporting evidence for potential legal challenge")
        
        if len(violations) > 10:
            recommendations.append("Consider filing a comprehensive motion addressing the multiple procedural violations")
        
        if actor_tracking:
            high_score_actors = [name for name, info in actor_tracking.items() if info.get('severity_score', 0) > 5]
            if high_score_actors:
                recommendations.append(f"Request recusal or investigation of repeat violators: {', '.join(high_score_actors[:3])}")
        
        timeline_violations = [v for v in violations if 'timeline' in v.get('type', '').lower()]
        if timeline_violations:
            recommendations.append("File motion addressing timeline and deadline violations")
        
        due_process_violations = [v for v in violations if 'due_process' in v.get('type', '').lower()]
        if due_process_violations:
            recommendations.append("Consider federal civil rights action under 42 U.S.C. § 1983 for due process violations")
        
        if not recommendations:
            recommendations.append("Continue monitoring case for procedural compliance")
            recommendations.append("Maintain detailed records of all court proceedings and communications")
        
        return recommendations
    
    def _calculate_risk_level(self, violations: List[Dict[str, Any]]) -> str:
        """Calculate overall case risk level"""
        if not violations:
            return "Low"
        
        high_count = len([v for v in violations if v.get('severity') == 'high'])
        medium_count = len([v for v in violations if v.get('severity') == 'medium'])
        
        if high_count >= 3:
            return "Critical"
        elif high_count >= 1 or medium_count >= 5:
            return "High"
        elif medium_count >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _get_severity_breakdown(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of violations by severity"""
        breakdown = {'high': 0, 'medium': 0, 'low': 0}
        for v in violations:
            severity = v.get('severity', 'low')
            breakdown[severity] += 1
        return breakdown