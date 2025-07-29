import json
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st

class CaseManager:
    """Manages complete legal case sessions with all documents, analysis, and findings"""
    
    def __init__(self):
        self.case_data_dir = Path("case_sessions")
        self.case_data_dir.mkdir(exist_ok=True)
        
    def create_case_session(self, case_name: str) -> str:
        """Create a new case session"""
        case_id = hashlib.md5(f"{case_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        case_session = {
            'case_id': case_id,
            'case_name': case_name,
            'created_date': datetime.now().isoformat(),
            'documents': {},
            'timeline': [],
            'entities': {
                'judges': set(),
                'attorneys': set(), 
                'caseworkers': set(),
                'children': set(),
                'case_numbers': set(),
                'courts': set()
            },
            'violations': [],
            'contradictions': [],
            'actor_tracking': {},
            'analysis_summary': {},
            'last_updated': datetime.now().isoformat()
        }
        
        return case_id, case_session
    
    def save_case_session(self, case_id: str, case_data: Dict[str, Any]):
        """Save case session to disk"""
        # Convert sets to lists for JSON serialization
        serializable_data = self._prepare_for_serialization(case_data.copy())
        
        case_file = self.case_data_dir / f"{case_id}.json"
        with open(case_file, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
    
    def load_case_session(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Load case session from disk"""
        case_file = self.case_data_dir / f"{case_id}.json"
        if case_file.exists():
            with open(case_file, 'r') as f:
                data = json.load(f)
            return self._prepare_from_serialization(data)
        return None
    
    def list_case_sessions(self) -> List[Dict[str, str]]:
        """List all available case sessions"""
        cases = []
        for case_file in self.case_data_dir.glob("*.json"):
            try:
                with open(case_file, 'r') as f:
                    data = json.load(f)
                cases.append({
                    'case_id': data['case_id'],
                    'case_name': data['case_name'],
                    'created_date': data['created_date'],
                    'last_updated': data.get('last_updated', data['created_date']),
                    'document_count': len(data.get('documents', {}))
                })
            except:
                continue
        
        return sorted(cases, key=lambda x: x['last_updated'], reverse=True)
    
    def add_document_to_case(self, case_data: Dict[str, Any], pdf_hash: str, 
                           document_analysis: Dict[str, Any], legal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add a processed document to the case"""
        doc_entry = {
            'pdf_hash': pdf_hash,
            'upload_date': datetime.now().isoformat(),
            'document_analysis': document_analysis,
            'legal_analysis': legal_analysis,
            'filename': document_analysis.get('filename', 'Unknown')
        }
        
        case_data['documents'][pdf_hash] = doc_entry
        
        # Update global entities
        if 'legal_entities' in legal_analysis:
            entities = legal_analysis['legal_entities']
            for entity_type, values in entities.items():
                if entity_type in case_data['entities']:
                    if isinstance(case_data['entities'][entity_type], set):
                        case_data['entities'][entity_type].update(values)
                    else:
                        case_data['entities'][entity_type] = set(case_data['entities'][entity_type] + values)
        
        # Update violations
        if 'potential_violations' in legal_analysis:
            for violation in legal_analysis['potential_violations']:
                violation['document_hash'] = pdf_hash
                violation['document_name'] = doc_entry['filename']
                case_data['violations'].append(violation)
        
        case_data['last_updated'] = datetime.now().isoformat()
        return case_data
    
    def generate_timeline(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate chronological timeline from all documents"""
        timeline_events = []
        
        for pdf_hash, doc in case_data['documents'].items():
            legal_analysis = doc['legal_analysis']
            
            # Extract dates and create timeline events
            if 'legal_entities' in legal_analysis and 'dates' in legal_analysis['legal_entities']:
                for date_str in legal_analysis['legal_entities']['dates']:
                    try:
                        # Parse various date formats
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            timeline_events.append({
                                'date': parsed_date,
                                'date_str': date_str,
                                'document': doc['filename'],
                                'document_hash': pdf_hash,
                                'document_type': legal_analysis.get('document_type', {}).get('type', 'unknown'),
                                'context': f"Referenced in {doc['filename']}"
                            })
                    except:
                        continue
        
        # Sort by date
        timeline_events.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
        case_data['timeline'] = timeline_events
        
        return timeline_events
    
    def detect_contradictions(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect contradictions and inconsistencies across documents"""
        contradictions = []
        documents = case_data['documents']
        
        # Check for date inconsistencies
        all_dates = {}
        for pdf_hash, doc in documents.items():
            legal_analysis = doc['legal_analysis']
            if 'legal_entities' in legal_analysis and 'dates' in legal_analysis['legal_entities']:
                for date_str in legal_analysis['legal_entities']['dates']:
                    if date_str not in all_dates:
                        all_dates[date_str] = []
                    all_dates[date_str].append({
                        'document': doc['filename'],
                        'hash': pdf_hash
                    })
        
        # Look for conflicting information
        case_numbers = {}
        for pdf_hash, doc in documents.items():
            legal_analysis = doc['legal_analysis']
            if 'legal_entities' in legal_analysis and 'case_numbers' in legal_analysis['legal_entities']:
                for case_num in legal_analysis['legal_entities']['case_numbers']:
                    if case_num not in case_numbers:
                        case_numbers[case_num] = []
                    case_numbers[case_num].append({
                        'document': doc['filename'],
                        'hash': pdf_hash
                    })
        
        # Flag potential contradictions
        for case_num, docs in case_numbers.items():
            if len(docs) > 1:
                # Multiple documents with same case number - could indicate inconsistency
                doc_types = set()
                for doc_info in docs:
                    doc_hash = doc_info['hash']
                    doc_type = documents[doc_hash]['legal_analysis'].get('document_type', {}).get('type', 'unknown')
                    doc_types.add(doc_type)
                
                if len(doc_types) > 1:
                    contradictions.append({
                        'type': 'case_number_inconsistency',
                        'severity': 'medium',
                        'description': f"Case number {case_num} appears in documents of different types",
                        'documents': [d['document'] for d in docs],
                        'case_number': case_num
                    })
        
        case_data['contradictions'] = contradictions
        return contradictions
    
    def track_repeat_actors(self, case_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Track judges, GALs, caseworkers who appear in multiple flagged documents"""
        actor_tracking = {}
        
        # Track violations by actor
        for violation in case_data['violations']:
            doc_hash = violation.get('document_hash', '')
            if doc_hash in case_data['documents']:
                legal_analysis = case_data['documents'][doc_hash]['legal_analysis']
                entities = legal_analysis.get('legal_entities', {})
                
                # Check judges
                for judge in entities.get('judge_names', []):
                    if judge not in actor_tracking:
                        actor_tracking[judge] = {
                            'type': 'judge',
                            'violations': [],
                            'documents': set(),
                            'severity_score': 0
                        }
                    
                    actor_tracking[judge]['violations'].append(violation)
                    actor_tracking[judge]['documents'].add(case_data['documents'][doc_hash]['filename'])
                    
                    # Add severity score
                    severity_scores = {'high': 3, 'medium': 2, 'low': 1}
                    actor_tracking[judge]['severity_score'] += severity_scores.get(violation.get('severity', 'low'), 1)
        
        # Convert sets to lists for serialization
        for actor in actor_tracking:
            actor_tracking[actor]['documents'] = list(actor_tracking[actor]['documents'])
        
        case_data['actor_tracking'] = actor_tracking
        return actor_tracking
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_formats = [
            "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
            "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
            "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        return None
    
    def _prepare_for_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert sets to lists for JSON serialization"""
        if 'entities' in data:
            for key, value in data['entities'].items():
                if isinstance(value, set):
                    data['entities'][key] = list(value)
        return data
    
    def _prepare_from_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert lists back to sets after JSON deserialization"""
        if 'entities' in data:
            for key, value in data['entities'].items():
                if isinstance(value, list):
                    data['entities'][key] = set(value)
        return data