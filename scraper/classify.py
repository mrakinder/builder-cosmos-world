"""
Seller classification module
===========================

Classifies sellers as owners or agencies based on text analysis and indicators.
"""

import re
import logging
from typing import Dict, List, Any
from .models import SellerClassificationResult

logger = logging.getLogger(__name__)

class SellerClassifier:
    """Classifier for determining if seller is owner or agency"""
    
    def __init__(self):
        # Owner keywords and patterns
        self.owner_keywords = [
            'власник', 'власниця', 'хазяїн', 'хазяйка',
            'приватна особа', 'приватний продавець',
            'без посередників', 'без агентів', 'без комісії',
            'від власника', 'власне житло',
            'продаю власну', 'здаю власну',
            'мій квартира', 'моя квартира'
        ]
        
        # Agency keywords and patterns
        self.agency_keywords = [
            'агентство', 'агент', 'ріелтор', 'рієлтор',
            'нерухомість', 'компанія', 'фірма',
            'послуги', 'допомога', 'консультація',
            'великий вибір', 'багато варіантів',
            'база даних', 'каталог',
            'ооо', 'тов', 'фоп', 'чп'
        ]
        
        # Owner phrases (more complex patterns)
        self.owner_phrases = [
            r'власник\s+(?:продає|здає)',
            r'(?:продам|здам).*власн',
            r'приватн.*особ',
            r'без.*посередник',
            r'власн.*житл'
        ]
        
        # Agency phrases
        self.agency_phrases = [
            r'агентств.*нерухомост',
            r'допомож.*продаж',
            r'професійн.*послуг',
            r'великий.*вибір',
            r'гарант.*безпек'
        ]
    
    def classify_seller(self, title: str, description: str, seller_name: str = None, 
                       seller_type_hint: str = None) -> SellerClassificationResult:
        """
        Classify seller based on available information
        
        Args:
            title: Property title
            description: Property description
            seller_name: Seller name if available
            seller_type_hint: Any type hint from website (e.g. "Приватна особа")
            
        Returns:
            SellerClassificationResult with classification and signals
        """
        
        signals = {}
        owner_score = 0.0
        agency_score = 0.0
        
        # Combine all text for analysis
        combined_text = f"{title} {description}".lower()
        if seller_name:
            combined_text += f" {seller_name.lower()}"
        
        # Check seller type hint first (highest priority)
        if seller_type_hint:
            hint_lower = seller_type_hint.lower()
            if 'приватна особа' in hint_lower or 'власник' in hint_lower:
                owner_score += 0.8
                signals['type_hint'] = seller_type_hint
            elif 'агентство' in hint_lower or 'компанія' in hint_lower:
                agency_score += 0.8
                signals['type_hint'] = seller_type_hint
        
        # Check owner keywords
        owner_matches = []
        for keyword in self.owner_keywords:
            if keyword in combined_text:
                owner_score += 0.3
                owner_matches.append(keyword)
        
        if owner_matches:
            signals['owner_keywords'] = owner_matches
        
        # Check agency keywords  
        agency_matches = []
        for keyword in self.agency_keywords:
            if keyword in combined_text:
                agency_score += 0.3
                agency_matches.append(keyword)
        
        if agency_matches:
            signals['agency_keywords'] = agency_matches
        
        # Check owner phrases (regex patterns)
        owner_phrase_matches = []
        for phrase_pattern in self.owner_phrases:
            matches = re.findall(phrase_pattern, combined_text, re.IGNORECASE)
            if matches:
                owner_score += 0.4
                owner_phrase_matches.extend(matches)
        
        if owner_phrase_matches:
            signals['owner_phrases'] = owner_phrase_matches
        
        # Check agency phrases
        agency_phrase_matches = []
        for phrase_pattern in self.agency_phrases:
            matches = re.findall(phrase_pattern, combined_text, re.IGNORECASE)
            if matches:
                agency_score += 0.4
                agency_phrase_matches.extend(matches)
        
        if agency_phrase_matches:
            signals['agency_phrases'] = agency_phrase_matches
        
        # Additional heuristics
        
        # Long descriptions with professional language often indicate agencies
        if len(description) > 500:
            professional_indicators = [
                'гарантуємо', 'професійно', 'досвід', 'експерт',
                'консультація', 'юридичний', 'документи'
            ]
            
            professional_count = sum(1 for indicator in professional_indicators 
                                   if indicator in combined_text)
            
            if professional_count >= 2:
                agency_score += 0.2
                signals['professional_language'] = professional_count
        
        # Multiple phone numbers often indicate agencies
        phone_pattern = r'(?:\+380|380|0)\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2}'
        phone_matches = re.findall(phone_pattern, combined_text)
        if len(phone_matches) > 1:
            agency_score += 0.2
            signals['multiple_phones'] = len(phone_matches)
        
        # Very similar formatting across multiple ads (future enhancement)
        # Could be implemented by comparing with previously seen ads
        
        # Determine final classification
        total_score = owner_score + agency_score
        
        if total_score == 0:
            # No clear indicators
            seller_type = 'unknown'
            confidence = 0.0
        elif owner_score > agency_score:
            seller_type = 'owner' 
            confidence = min(owner_score / max(total_score, 1.0), 1.0)
        else:
            seller_type = 'agency'
            confidence = min(agency_score / max(total_score, 1.0), 1.0)
        
        # Add scoring details to signals
        signals['owner_score'] = round(owner_score, 2)
        signals['agency_score'] = round(agency_score, 2)
        signals['total_score'] = round(total_score, 2)
        
        logger.debug(f"Seller classification: {seller_type} (confidence: {confidence:.2f})")
        logger.debug(f"Signals: {signals}")
        
        return SellerClassificationResult(
            seller_type=seller_type,
            confidence=confidence,
            signals=signals
        )
    
    def bulk_classify(self, properties: List[Dict[str, Any]]) -> List[SellerClassificationResult]:
        """
        Classify multiple properties in bulk
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of classification results
        """
        results = []
        
        for prop in properties:
            result = self.classify_seller(
                title=prop.get('title', ''),
                description=prop.get('description', ''),
                seller_name=prop.get('seller_name'),
                seller_type_hint=prop.get('seller_type_hint')
            )
            results.append(result)
        
        return results
    
    def update_classification_rules(self, new_owner_keywords: List[str] = None,
                                  new_agency_keywords: List[str] = None):
        """
        Update classification rules with new keywords
        
        Args:
            new_owner_keywords: Additional owner keywords
            new_agency_keywords: Additional agency keywords
        """
        if new_owner_keywords:
            self.owner_keywords.extend(new_owner_keywords)
            logger.info(f"Added {len(new_owner_keywords)} new owner keywords")
        
        if new_agency_keywords:
            self.agency_keywords.extend(new_agency_keywords)
            logger.info(f"Added {len(new_agency_keywords)} new agency keywords")
