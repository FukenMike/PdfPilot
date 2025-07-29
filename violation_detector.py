import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from openai import OpenAI

class ViolationDetector:
    """Advanced violation detection for legal documents with severity scoring"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Comprehensive violation patterns with severity levels
        self.violation_patterns = {
            # High Severity Violations
            'constitutional_violation': {
                'patterns': [
                    r'constitutional\s+violation',
                    r'fourteenth\s+amendment\s+violation',
                    r'due\s+process\s+violation',
                    r'equal\s+protection\s+violation'
                ],
                'severity': 'high',
                'description': 'Constitutional rights violation'
            },
            'removal_without_court_order': {
                'patterns': [
                    r'removed?\s+without\s+(?:court\s+)?order',
                    r'emergency\s+removal\s+without\s+hearing',
                    r'taken\s+into\s+custody\s+without\s+warrant'
                ],
                'severity': 'high',
                'description': 'Child removed without proper court authorization'
            },
            'due_process_denial': {
                'patterns': [
                    r'denied\s+(?:due\s+)?process',
                    r'no\s+notice\s+provided',
                    r'insufficient\s+notice',
                    r'ex\s+parte\s+proceeding'
                ],
                'severity': 'high',
                'description': 'Due process rights denied'
            },
            
            # Medium Severity Violations
            'delayed_icpc': {
                'patterns': [
                    r'icpc\s+delay',
                    r'interstate\s+compact\s+violation',
                    r'delayed\s+placement\s+approval',
                    r'icpc\s+not\s+completed'
                ],
                'severity': 'medium',
                'description': 'Delayed ICPC processing affecting placement'
            },
            'missed_hearing': {
                'patterns': [
                    r'hearing\s+not\s+held',
                    r'missed\s+hearing',
                    r'hearing\s+postponed\s+repeatedly',
                    r'no\s+permanency\s+hearing'
                ],
                'severity': 'medium',
                'description': 'Required hearings missed or delayed'
            },
            'inadequate_reunification': {
                'patterns': [
                    r'no\s+reunification\s+efforts?',
                    r'insufficient\s+reunification',
                    r'failed\s+to\s+provide\s+services',
                    r'reunification\s+not\s+attempted'
                ],
                'severity': 'medium',
                'description': 'Inadequate or missing reunification efforts'
            },
            'procedural_error': {
                'patterns': [
                    r'procedural\s+error',
                    r'improper\s+procedure',
                    r'failed\s+to\s+follow\s+protocol',
                    r'statutory\s+violation'
                ],
                'severity': 'medium',
                'description': 'Procedural or statutory requirements not followed'
            },
            
            # Low Severity Violations  
            'documentation_error': {
                'patterns': [
                    r'missing\s+documentation',
                    r'incomplete\s+records',
                    r'filing\s+error',
                    r'administrative\s+error'
                ],
                'severity': 'low',
                'description': 'Documentation or administrative errors'
            },
            'timeline_violation': {
                'patterns': [
                    r'deadline\s+missed',
                    r'untimely\s+filing',
                    r'late\s+submission',
                    r'time\s+limit\s+exceeded'
                ],
                'severity': 'low',
                'description': 'Timeline or deadline violations'
            }
        }
        
        # CPS/DHR specific violations
        self.cps_violations = {
            'safety_plan_violation': {
                'patterns': [
                    r'safety\s+plan\s+not\s+followed',
                    r'violated\s+safety\s+plan',
                    r'safety\s+plan\s+breach'
                ],
                'severity': 'high',
                'description': 'Safety plan violations'
            },
            'visitation_denial': {
                'patterns': [
                    r'visitation\s+denied',
                    r'denied\s+access\s+to\s+child',
                    r'supervised\s+visitation\s+cancelled',
                    r'no\s+visitation\s+allowed'
                ],
                'severity': 'medium',
                'description': 'Improper denial of parent-child contact'
            },
            'case_plan_violation': {
                'patterns': [
                    r'case\s+plan\s+not\s+followed',
                    r'isp\s+violation',
                    r'service\s+plan\s+breach',
                    r'treatment\s+plan\s+ignored'
                ],
                'severity': 'medium',
                'description': 'Case plan or ISP requirements not met'
            }
        }
        
        # Family court specific violations
        self.family_court_violations = {
            'custody_order_violation': {
                'patterns': [
                    r'custody\s+order\s+violated',
                    r'parenting\s+time\s+denied',
                    r'contempt\s+of\s+court',
                    r'order\s+not\s+followed'
                ],
                'severity': 'medium',
                'description': 'Court custody orders not followed'
            },
            'judicial_bias': {
                'patterns': [
                    r'judicial\s+bias',
                    r'prejudiced\s+judge',
                    r'biased\s+ruling',
                    r'conflict\s+of\s+interest'
                ],
                'severity': 'high',
                'description': 'Evidence of judicial bias or conflict'
            }
        }
        
    def detect_violations(self, text: str, document_type: str = 'unknown') -> List[Dict[str, Any]]:
        """Detect violations in document text with severity scoring"""
        violations = []
        text_lower = text.lower()
        
        # Get relevant violation patterns based on document type
        all_patterns = {**self.violation_patterns}
        
        if 'cps' in document_type.lower() or any(term in text_lower for term in ['cps', 'child protective', 'dhr']):
            all_patterns.update(self.cps_violations)
            
        if 'custody' in document_type.lower() or 'family court' in text_lower:
            all_patterns.update(self.family_court_violations)
        
        # Search for violation patterns
        for violation_type, violation_info in all_patterns.items():
            for pattern in violation_info['patterns']:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    # Get context around the match
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    violations.append({
                        'type': violation_type,
                        'description': violation_info['description'],
                        'severity': violation_info['severity'],
                        'context': context,
                        'pattern_matched': match.group(),
                        'position': {
                            'start': match.start(),
                            'end': match.end()
                        },
                        'severity_score': self._get_severity_score(violation_info['severity'])
                    })
        
        # Remove duplicates and sort by severity
        violations = self._deduplicate_violations(violations)
        violations.sort(key=lambda x: x['severity_score'], reverse=True)
        
        return violations
    
    def analyze_timeline_violations(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze timeline for procedural violations and delays"""
        timeline_violations = []
        
        if len(timeline) < 2:
            return timeline_violations
        
        # Check for excessive delays between events
        for i in range(1, len(timeline)):
            current_event = timeline[i]
            previous_event = timeline[i-1]
            
            if current_event['date'] and previous_event['date']:
                time_diff = current_event['date'] - previous_event['date']
                
                # Flag excessive delays (more than 6 months between court events)
                if time_diff.days > 180:
                    timeline_violations.append({
                        'type': 'excessive_delay',
                        'severity': 'medium',
                        'severity_score': 2,
                        'description': f'Excessive delay ({time_diff.days} days) between events',
                        'context': f"From {previous_event['document']} to {current_event['document']}",
                        'time_difference': time_diff.days,
                        'events': [previous_event, current_event]
                    })
        
        return timeline_violations
    
    def advanced_violation_analysis(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Use AI for advanced violation pattern detection"""
        if development_mode:
            return {
                'advanced_violations': '[DEV MODE] Advanced AI violation analysis disabled',
                'patterns_detected': ['Development mode active'],
                'recommendations': ['Enable production mode for AI-powered violation detection']
            }
        
        try:
            prompt = f"""
            As a legal expert specializing in family court and child welfare cases, analyze this document for sophisticated legal violations that may not be obvious from simple pattern matching. Focus on:

            1. Procedural due process violations
            2. Constitutional issues (4th, 5th, 14th Amendment violations)
            3. Statutory timeline violations
            4. Evidence of judicial bias or misconduct
            5. CPS/DHR procedural failures
            6. Custody order violations
            7. ICPC compliance issues
            8. Reunification effort adequacy
            9. Discovery violations
            10. Ex parte communication issues

            Document text (first 3000 characters):
            {text[:3000]}

            Provide analysis in JSON format with specific violations, severity levels, and legal citations where applicable.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal expert specializing in identifying procedural violations and constitutional issues in family court and child welfare cases. Provide detailed analysis with specific legal reasoning."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            try:
                import json
                return json.loads(response.choices[0].message.content)
            except:
                return {
                    'analysis': response.choices[0].message.content,
                    'format': 'text'
                }
                
        except Exception as e:
            return {
                'error': f'Advanced violation analysis failed: {str(e)}',
                'recommendations': ['Check API configuration and try again']
            }
    
    def generate_violation_heatmap_data(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate data for violation severity heatmap"""
        heatmap_data = {
            'severity_counts': {'high': 0, 'medium': 0, 'low': 0},
            'violation_types': {},
            'total_score': 0,
            'risk_level': 'low'
        }
        
        for violation in violations:
            severity = violation.get('severity', 'low')
            v_type = violation.get('type', 'unknown')
            
            heatmap_data['severity_counts'][severity] += 1
            
            if v_type not in heatmap_data['violation_types']:
                heatmap_data['violation_types'][v_type] = {
                    'count': 0,
                    'severity': severity,
                    'description': violation.get('description', '')
                }
            heatmap_data['violation_types'][v_type]['count'] += 1
            
            heatmap_data['total_score'] += violation.get('severity_score', 1)
        
        # Determine overall risk level
        if heatmap_data['severity_counts']['high'] >= 3:
            heatmap_data['risk_level'] = 'critical'
        elif heatmap_data['severity_counts']['high'] >= 1 or heatmap_data['severity_counts']['medium'] >= 5:
            heatmap_data['risk_level'] = 'high'
        elif heatmap_data['severity_counts']['medium'] >= 2:
            heatmap_data['risk_level'] = 'medium'
        
        return heatmap_data
    
    def _get_severity_score(self, severity: str) -> int:
        """Convert severity to numeric score"""
        scores = {'high': 3, 'medium': 2, 'low': 1}
        return scores.get(severity, 1)
    
    def _deduplicate_violations(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate violations based on type and context similarity"""
        seen = set()
        deduplicated = []
        
        for violation in violations:
            # Create a key based on type and first 50 chars of context
            key = f"{violation['type']}_{violation.get('context', '')[:50]}"
            if key not in seen:
                seen.add(key)
                deduplicated.append(violation)
        
        return deduplicated