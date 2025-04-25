import re
from urllib.parse import urlparse

def validate_url(url):
    """
    Validate URL format
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not url:
        return False
    
    # Add http:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
        
def validate_budget(budget):
    """
    Validate budget input
    
    Args:
        budget (str): Budget amount as string
    
    Returns:
        tuple: (valid (bool), value (float) if valid, else None)
    """
    if not budget:
        return False, None
    
    # Remove non-numeric characters except decimal point
    budget = re.sub(r'[^\d.]', '', budget)
    
    try:
        value = float(budget)
        if value <= 0:
            return False, None
        return True, value
    except:
        return False, None
