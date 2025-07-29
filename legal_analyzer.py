import re
import json
from datetime import datetime
from typing import Dict, List, Any
import os
from openai import OpenAI

class LegalDocumentAnalyzer:
    """Specialized analyzer for legal documents with focus on case files and judicial proceedings"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Legal document patterns
        self.legal_patterns = {
            'case_numbers': r'(?:Case|No\.|#)\s*:?\s*([A-Z0-9\-]+)',
            'court_names': r'(?:IN THE|BEFORE THE)\s+([A-Z\s]+(?:COURT|TRIBUNAL))',
            'dates': r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})\b',
            'judge_names': r'(?:JUDGE|HON\.|HONORABLE)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'attorney_names': r'(?:ATTORNEY|COUNSEL|ESQ\.)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'motions': r'(MOTION\s+(?:FOR|TO)\s+[A-Z\s]+)',
            'orders': r'(ORDER\s+(?:FOR|TO|OF)\s+[A-Z\s]+)',
            'violations': r'(VIOLATION\s+OF\s+[A-Z\s]+|DUE\s+PROCESS\s+VIOLATION)',
            'deadlines': r'(?:DEADLINE|DUE\s+BY|MUST\s+BE\s+FILED)\s*:?\s*([A-Z0-9\s,]+)',
            'custody_terms': r'(CUSTODY|VISITATION|PARENTING\s+TIME|CHILD\s+SUPPORT)',
            'cps_terms': r'(CPS|CHILD\s+PROTECTIVE\s+SERVICES|DHR|DEPARTMENT\s+OF\s+HUMAN\s+RESOURCES)',
            'isp_terms': r'(ISP|INDIVIDUALIZED\s+SERVICE\s+PLAN|CASE\s+PLAN)'
        }
        
        # Legal violation indicators
        self.violation_indicators = [
            'due process violation',
            'constitutional violation',
            'procedural error',
            'jurisdictional issue',
            'inadequate representation',
            'failure to provide notice',
            'ex parte communication',
            'bias or prejudice',
            'insufficient evidence',
            'improper venue',
            'statute of limitations',
            'discovery violation',
            'brady violation',
            'ineffective assistance'
        ]
        
        # Document type classifiers
        self.document_types = {
            'petition': ['petition', 'complaint', 'filing'],
            'motion': ['motion', 'request', 'application'],
            'order': ['order', 'judgment', 'decree', 'ruling'],
            'pleading': ['answer', 'response', 'reply', 'counter'],
            'evidence': ['exhibit', 'affidavit', 'declaration', 'testimony'],
            'custody': ['custody', 'visitation', 'parenting', 'child support'],
            'cps': ['cps', 'child protective', 'dhr', 'removal', 'placement'],
            'isp': ['service plan', 'case plan', 'treatment plan', 'goals']
        }
    
    def analyze_document_type(self, text: str) -> Dict[str, Any]:
        """Classify the type of legal document"""
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in self.document_types.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            if score > 0:
                scores[doc_type] = score
        
        if not scores:
            return {'type': 'unknown', 'confidence': 0.0}
        
        primary_type = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[primary_type] / total_score
        
        return {
            'type': primary_type,
            'confidence': confidence,
            'all_scores': scores
        }
    
    def extract_legal_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal entities like case numbers, dates, names, etc."""
        entities = {}
        
        for entity_type, pattern in self.legal_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean and deduplicate matches
                clean_matches = list(set([match.strip() for match in matches if match.strip()]))
                entities[entity_type] = clean_matches
        
        return entities
    
    def detect_potential_violations(self, text: str) -> List[Dict[str, Any]]:
        """Detect potential legal violations or procedural issues"""
        violations = []
        text_lower = text.lower()
        
        for indicator in self.violation_indicators:
            if indicator in text_lower:
                # Find context around the violation
                pattern = rf'.{{0,100}}{re.escape(indicator)}.{{0,100}}'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    violations.append({
                        'type': indicator,
                        'context': match.strip(),
                        'severity': self._assess_violation_severity(indicator)
                    })
        
        return violations
    
    def _assess_violation_severity(self, violation_type: str) -> str:
        """Assess the severity of a potential violation"""
        high_severity = ['constitutional violation', 'due process violation', 'brady violation']
        medium_severity = ['procedural error', 'discovery violation', 'inadequate representation']
        
        if violation_type in high_severity:
            return 'high'
        elif violation_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def analyze_custody_case(self, text: str) -> Dict[str, Any]:
        """Specialized analysis for custody cases"""
        analysis = {
            'case_type': 'custody',
            'key_issues': [],
            'parties': [],
            'children_mentioned': [],
            'custody_arrangements': [],
            'support_orders': []
        }
        
        # Look for custody-specific patterns
        custody_patterns = {
            'physical_custody': r'physical\s+custody',
            'legal_custody': r'legal\s+custody',
            'joint_custody': r'joint\s+custody',
            'sole_custody': r'sole\s+custody',
            'visitation': r'visitation|parenting\s+time',
            'child_support': r'child\s+support|\$\d+.*(?:month|week)',
            'best_interest': r'best\s+interest\s+of\s+(?:the\s+)?child'
        }
        
        for issue, pattern in custody_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                analysis['key_issues'].append(issue)
        
        return analysis
    
    def analyze_cps_case(self, text: str) -> Dict[str, Any]:
        """Specialized analysis for CPS/DHR cases"""
        analysis = {
            'case_type': 'cps',
            'allegations': [],
            'safety_concerns': [],
            'service_plans': [],
            'court_orders': [],
            'timeline_issues': []
        }
        
        # CPS-specific patterns
        cps_patterns = {
            'neglect': r'neglect|failure\s+to\s+provide',
            'abuse': r'abuse|physical\s+harm|sexual\s+abuse',
            'abandonment': r'abandon|left\s+unattended',
            'substance_abuse': r'drug|alcohol|substance\s+abuse',
            'domestic_violence': r'domestic\s+violence|family\s+violence',
            'removal': r'removal|taken\s+into\s+custody',
            'placement': r'placement|foster\s+care|kinship',
            'reunification': r'reunification|return\s+home'
        }
        
        for concern, pattern in cps_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                analysis['allegations'].append(concern)
        
        return analysis
    
    def find_procedural_flaws(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Identify potential procedural flaws and due process violations"""
        if development_mode:
            return {
                'procedural_analysis': '[DEV MODE] Procedural analysis would identify timeline violations, notice issues, and due process concerns',
                'potential_flaws': ['Development mode active - no actual analysis performed'],
                'recommendations': ['Enable production mode for full legal analysis']
            }
        
        try:
            # Use GPT-4o for sophisticated legal analysis
            prompt = f"""
            As a legal analyst specializing in family court and child welfare cases, analyze this document for potential procedural flaws, due process violations, and judicial malpractice indicators. Focus on:

            1. Timeline violations and missed deadlines
            2. Inadequate notice or service issues
            3. Due process violations
            4. Jurisdictional problems
            5. Evidentiary issues
            6. Constitutional violations
            7. Procedural irregularities

            Document text:
            {text[:4000]}  # Limit text to avoid token limits

            Provide analysis in JSON format with specific findings and recommendations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal analyst specializing in identifying procedural flaws and due process violations in family court and child welfare cases. Provide detailed, actionable analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(response.choices[0].message.content)
            except:
                return {
                    'analysis': response.choices[0].message.content,
                    'format': 'text'
                }
                
        except Exception as e:
            return {
                'error': f'Legal analysis failed: {str(e)}',
                'recommendations': ['Check API configuration and try again']
            }
    
    def comprehensive_legal_analysis(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Perform comprehensive legal document analysis"""
        
        # Basic document analysis
        doc_type = self.analyze_document_type(text)
        entities = self.extract_legal_entities(text)
        violations = self.detect_potential_violations(text)
        
        # Specialized analysis based on document type
        specialized_analysis = {}
        if 'custody' in text.lower() or doc_type['type'] == 'custody':
            specialized_analysis = self.analyze_custody_case(text)
        elif any(term in text.lower() for term in ['cps', 'child protective', 'dhr']):
            specialized_analysis = self.analyze_cps_case(text)
        
        # Procedural analysis
        procedural_analysis = self.find_procedural_flaws(text, development_mode)
        
        return {
            'document_type': doc_type,
            'legal_entities': entities,
            'potential_violations': violations,
            'specialized_analysis': specialized_analysis,
            'procedural_analysis': procedural_analysis,
            'analysis_timestamp': datetime.now().isoformat()
        }