"""
Seller Classification Module
Classifies property sellers as 'owner' or 'agency' based on keywords and patterns
"""

import re
from typing import Optional
from .config import OWNER_KEYWORDS, AGENCY_KEYWORDS


def classify_seller(title: str, description: str = "") -> str:
    """
    Classify seller as 'owner' or 'agency' based on title and description
    
    Args:
        title: Property listing title
        description: Property description (optional)
        
    Returns:
        str: 'owner' or 'agency'
    """
    text = (title + " " + description).lower()
    
    # Count owner indicators
    owner_score = 0
    for keyword in OWNER_KEYWORDS:
        if keyword.lower() in text:
            owner_score += 1
    
    # Count agency indicators
    agency_score = 0
    for keyword in AGENCY_KEYWORDS:
        if keyword.lower() in text:
            agency_score += 1
    
    # Additional patterns for owners
    owner_patterns = [
        r'\bвід\s+власника\b',
        r'\bбез\s+посередник\w*\b',
        r'\bособисто\b',
        r'\bхазя\w+\b',
        r'\bбез\s+комісі\w*\b',
        r'\bприватна\s+особа\b'
    ]
    
    for pattern in owner_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            owner_score += 2
    
    # Additional patterns for agencies
    agency_patterns = [
        r'\b(агентств|ріелтор|realtor|estate)\w*\b',
        r'\b(ТОВ|ПП|ООО|компанія)\b',
        r'\b(центр\s+нерухомості|операції\s+з\s+нерухомістю)\b',
        r'\b(професійний\s+ріелтор|licensed\s+agent)\b'
    ]
    
    for pattern in agency_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            agency_score += 2
    
    # Decision logic
    if owner_score > agency_score:
        return "owner"
    elif agency_score > owner_score:
        return "agency"
    else:
        # Default to agency if unclear (more conservative)
        return "agency"


def get_classification_confidence(title: str, description: str = "") -> float:
    """
    Get confidence score for seller classification (0.0 to 1.0)
    
    Args:
        title: Property listing title
        description: Property description
        
    Returns:
        float: Confidence score
    """
    text = (title + " " + description).lower()
    
    # Count all indicators
    total_indicators = 0
    
    for keyword in OWNER_KEYWORDS + AGENCY_KEYWORDS:
        if keyword.lower() in text:
            total_indicators += 1
    
    # More indicators = higher confidence
    if total_indicators >= 3:
        return 0.9
    elif total_indicators == 2:
        return 0.7
    elif total_indicators == 1:
        return 0.5
    else:
        return 0.3


def extract_seller_info(text: str) -> Optional[str]:
    """
    Extract specific seller information from text
    
    Args:
        text: Text to analyze
        
    Returns:
        Optional[str]: Extracted seller info or None
    """
    text_lower = text.lower()
    
    # Look for phone patterns that might indicate direct owner
    phone_patterns = [
        r'\+380\d{9}',
        r'0\d{2}\s?\d{3}\s?\d{4}',
        r'\b\d{3}-\d{3}-\d{4}\b'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return f"Phone: {match.group()}"
    
    # Look for company names
    company_patterns = [
        r'(ТОВ|ПП|ООО)\s+"[^"]+"',
        r'(агентство|центр)\s+["""][^"""]+["""]',
        r'компанія\s+"[^"]+"'
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"Company: {match.group()}"
    
    return None
