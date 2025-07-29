import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
from openai import OpenAI
import json

class GlobalSearch:
    """Advanced search across all documents in a case with semantic and pattern-based capabilities"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Legal search patterns
        self.legal_patterns = {
            'due_process': [
                r'due\s+process',
                r'procedural\s+due\s+process',
                r'substantive\s+due\s+process',
                r'fourteenth\s+amendment'
            ],
            'constitutional': [
                r'constitutional\s+(?:rights?|violation)',
                r'first\s+amendment',
                r'fourth\s+amendment',
                r'fifth\s+amendment',
                r'fourteenth\s+amendment'
            ],
            'custody_violations': [
                r'custody\s+(?:violation|interference)',
                r'parental\s+alienation',
                r'denial\s+of\s+(?:access|visitation)',
                r'contempt\s+of\s+court'
            ],
            'cps_violations': [
                r'false\s+allegations?',
                r'malicious\s+reporting',
                r'improper\s+removal',
                r'safety\s+plan\s+violation'
            ],
            'judicial_misconduct': [
                r'judicial\s+(?:bias|misconduct|malpractice)',
                r'conflict\s+of\s+interest',
                r'ex\s+parte\s+communication',
                r'prejudiced\s+ruling'
            ]
        }
    
    def search_all_documents(self, case_data: Dict[str, Any], query: str, 
                           search_type: str = 'comprehensive') -> Dict[str, Any]:
        """Search across all documents in a case"""
        documents = case_data.get('documents', {})
        
        if not documents:
            return {'results': [], 'total_matches': 0, 'query': query}
        
        results = []
        
        if search_type == 'text_only':
            results = self._text_search(documents, query)
        elif search_type == 'pattern_based':
            results = self._pattern_search(documents, query)
        elif search_type == 'semantic':
            results = self._semantic_search(documents, query, case_data.get('development_mode', False))
        else:  # comprehensive
            # Combine all search methods
            text_results = self._text_search(documents, query)
            pattern_results = self._pattern_search(documents, query)
            semantic_results = self._semantic_search(documents, query, case_data.get('development_mode', False))
            
            # Merge and deduplicate results
            all_results = text_results + pattern_results + semantic_results
            results = self._deduplicate_search_results(all_results)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return {
            'results': results[:50],  # Limit to top 50 results
            'total_matches': len(results),
            'query': query,
            'search_type': search_type,
            'timestamp': datetime.now().isoformat()
        }
    
    def search_violations(self, case_data: Dict[str, Any], violation_type: str = 'all') -> Dict[str, Any]:
        """Search for specific types of violations across all documents"""
        violations = case_data.get('violations', [])
        
        if violation_type == 'all':
            filtered_violations = violations
        else:
            filtered_violations = [v for v in violations if v.get('type', '').lower() == violation_type.lower()]
        
        # Group by document
        violation_by_doc = {}
        for violation in filtered_violations:
            doc_hash = violation.get('document_hash', 'unknown')
            if doc_hash not in violation_by_doc:
                violation_by_doc[doc_hash] = {
                    'document_name': violation.get('document_name', 'Unknown'),
                    'violations': []
                }
            violation_by_doc[doc_hash]['violations'].append(violation)
        
        # Calculate statistics
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for violation in filtered_violations:
            severity = violation.get('severity', 'low')
            severity_counts[severity] += 1
        
        return {
            'violation_type': violation_type,
            'total_violations': len(filtered_violations),
            'severity_breakdown': severity_counts,
            'violations_by_document': violation_by_doc,
            'timestamp': datetime.now().isoformat()
        }
    
    def search_actors(self, case_data: Dict[str, Any], actor_name: str = '', actor_type: str = 'all') -> Dict[str, Any]:
        """Search for specific actors (judges, attorneys, caseworkers) across documents"""
        actor_tracking = case_data.get('actor_tracking', {})
        entities = case_data.get('entities', {})
        
        results = {}
        
        if actor_name:
            # Search for specific actor
            for actor, info in actor_tracking.items():
                if actor_name.lower() in actor.lower():
                    results[actor] = info
        else:
            # Return all actors of specific type
            if actor_type == 'all':
                results = actor_tracking
            else:
                results = {actor: info for actor, info in actor_tracking.items() 
                          if info.get('type', '').lower() == actor_type.lower()}
        
        return {
            'actor_name': actor_name,
            'actor_type': actor_type,
            'results': results,
            'total_found': len(results),
            'timestamp': datetime.now().isoformat()
        }
    
    def search_timeline(self, case_data: Dict[str, Any], date_range: Optional[Tuple[datetime, datetime]] = None,
                       event_type: str = 'all') -> Dict[str, Any]:
        """Search timeline events with optional date range and event type filters"""
        timeline = case_data.get('timeline', [])
        
        filtered_events = timeline
        
        # Apply date range filter
        if date_range:
            start_date, end_date = date_range
            filtered_events = [
                event for event in filtered_events
                if event.get('date') and start_date <= event['date'] <= end_date
            ]
        
        # Apply event type filter
        if event_type != 'all':
            filtered_events = [
                event for event in filtered_events
                if event.get('document_type', '').lower() == event_type.lower()
            ]
        
        return {
            'date_range': date_range,
            'event_type': event_type,
            'events': filtered_events,
            'total_events': len(filtered_events),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_search_suggestions(self, case_data: Dict[str, Any]) -> List[str]:
        """Generate relevant search suggestions based on case content"""
        suggestions = []
        
        # Based on violations found
        violations = case_data.get('violations', [])
        violation_types = set(v.get('type', '') for v in violations)
        
        for v_type in list(violation_types)[:5]:  # Top 5 violation types
            suggestions.append(f"All instances of {v_type.replace('_', ' ')}")
        
        # Based on entities
        entities = case_data.get('entities', {})
        if entities.get('judges'):
            judges = list(entities['judges'])[:3]
            for judge in judges:
                suggestions.append(f"All rulings by Judge {judge}")
        
        if entities.get('case_numbers'):
            case_nums = list(entities['case_numbers'])[:2]
            for case_num in case_nums:
                suggestions.append(f"Case number {case_num}")
        
        # Legal pattern suggestions
        legal_suggestions = [
            "Due process violations",
            "Constitutional violations", 
            "Timeline violations",
            "Custody order violations",
            "CPS procedural errors",
            "Judicial bias indicators",
            "Missing documentation",
            "Delayed hearings"
        ]
        
        suggestions.extend(legal_suggestions[:8])
        
        return suggestions[:15]  # Return top 15 suggestions
    
    def _text_search(self, documents: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Simple text-based search"""
        results = []
        query_lower = query.lower()
        
        for doc_hash, doc_info in documents.items():
            # Search in cached text if available
            text = ""
            if 'document_analysis' in doc_info and 'extracted_text' in doc_info['document_analysis']:
                text = doc_info['document_analysis']['extracted_text']
            
            if query_lower in text.lower():
                # Find all matches and their contexts
                text_lower = text.lower()
                start_pos = 0
                
                while True:
                    pos = text_lower.find(query_lower, start_pos)
                    if pos == -1:
                        break
                    
                    # Get context around match
                    context_start = max(0, pos - 100)
                    context_end = min(len(text), pos + len(query) + 100)
                    context = text[context_start:context_end].strip()
                    
                    results.append({
                        'document_hash': doc_hash,
                        'document_name': doc_info.get('filename', 'Unknown'),
                        'match_type': 'text',
                        'context': context,
                        'position': pos,
                        'query': query,
                        'relevance_score': 1.0
                    })
                    
                    start_pos = pos + len(query)
        
        return results
    
    def _pattern_search(self, documents: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Pattern-based search using legal patterns"""
        results = []
        
        # Check if query matches any predefined legal patterns
        matching_patterns = []
        query_lower = query.lower()
        
        for pattern_category, patterns in self.legal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matching_patterns.extend(patterns)
                    break
        
        if not matching_patterns:
            return results
        
        for doc_hash, doc_info in documents.items():
            text = ""
            if 'document_analysis' in doc_info and 'extracted_text' in doc_info['document_analysis']:
                text = doc_info['document_analysis']['extracted_text']
            
            for pattern in matching_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 100)
                    context = text[context_start:context_end].strip()
                    
                    results.append({
                        'document_hash': doc_hash,
                        'document_name': doc_info.get('filename', 'Unknown'),
                        'match_type': 'pattern',
                        'context': context,
                        'pattern': pattern,
                        'matched_text': match.group(),
                        'query': query,
                        'relevance_score': 2.0  # Higher score for pattern matches
                    })
        
        return results
    
    def _semantic_search(self, documents: Dict[str, Any], query: str, development_mode: bool = False) -> List[Dict[str, Any]]:
        """AI-powered semantic search"""
        if development_mode:
            return [{
                'document_hash': 'dev_mode',
                'document_name': 'Development Mode Active',
                'match_type': 'semantic',
                'context': '[DEV MODE] Semantic search would use AI to find conceptually related content',
                'query': query,
                'relevance_score': 0.5
            }]
        
        results = []
        
        try:
            # Use GPT to find semantically relevant content
            for doc_hash, doc_info in documents.items():
                text = ""
                if 'document_analysis' in doc_info and 'extracted_text' in doc_info['document_analysis']:
                    text = doc_info['document_analysis']['extracted_text'][:3000]  # Limit for API
                
                if not text.strip():
                    continue
                
                prompt = f"""
                Search this legal document for content semantically related to: "{query}"
                
                Find passages that:
                1. Directly mention the topic
                2. Are conceptually related
                3. Provide relevant context
                4. May contain related legal issues
                
                Document text:
                {text}
                
                Return up to 3 most relevant passages with their context. Format as JSON:
                {{"passages": [{{"text": "relevant passage", "relevance": 0.8, "reason": "why relevant"}}]}}
                """
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a legal document search expert. Find the most relevant passages for the given query."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.3
                )
                
                try:
                    semantic_results = json.loads(response.choices[0].message.content)
                    for passage in semantic_results.get('passages', []):
                        results.append({
                            'document_hash': doc_hash,
                            'document_name': doc_info.get('filename', 'Unknown'),
                            'match_type': 'semantic',
                            'context': passage.get('text', ''),
                            'relevance_reason': passage.get('reason', ''),
                            'query': query,
                            'relevance_score': passage.get('relevance', 0.5) * 3  # Higher weight for semantic matches
                        })
                except:
                    # Fallback to simple AI response
                    if 'relevant' in response.choices[0].message.content.lower():
                        results.append({
                            'document_hash': doc_hash,
                            'document_name': doc_info.get('filename', 'Unknown'),
                            'match_type': 'semantic',
                            'context': response.choices[0].message.content[:200],
                            'query': query,
                            'relevance_score': 1.5
                        })
        
        except Exception as e:
            # Return error indicator for semantic search
            results.append({
                'document_hash': 'error',
                'document_name': 'Semantic Search Error',
                'match_type': 'error',
                'context': f'Semantic search failed: {str(e)}',
                'query': query,
                'relevance_score': 0.1
            })
        
        return results
    
    def _deduplicate_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results"""
        seen = set()
        deduplicated = []
        
        for result in results:
            # Create key based on document and context
            key = f"{result.get('document_hash', '')}_{result.get('context', '')[:50]}"
            if key not in seen:
                seen.add(key)
                deduplicated.append(result)
        
        return deduplicated