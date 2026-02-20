import math
import re
import string

def calculate_entropy(password):
    """
    Calculate the actual entropy of a password based on the character sets used.
    Entropy = log2(R^L) where R is the size of the character set and L is the length.
    """
    if not password:
        return 0
    
    # Determine the character set used in the password
    charset_size = 0
    
    # Check for different character types
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_digits = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))
    
    # Calculate the effective character set size
    if has_lowercase:
        charset_size += 26  # a-z
    if has_uppercase:
        charset_size += 26  # A-Z
    if has_digits:
        charset_size += 10  # 0-9
    if has_special:
        charset_size += 32  # Common special characters
    
    # If no character set detected, default to lowercase
    if charset_size == 0:
        charset_size = 26
    
    # Calculate entropy: log2(R^L) = L * log2(R)
    entropy = len(password) * math.log2(charset_size) if charset_size > 0 else 0
    
    return entropy

def entropy_to_strength(entropy):
    """
    Convert entropy value to a strength rating.
    """
    if entropy < 28:
        return "Very Weak", "red"
    elif entropy < 35:
        return "Weak", "orange"
    elif entropy < 50:
        return "Fair", "yellow"
    elif entropy < 65:
        return "Good", "lightgreen"
    elif entropy < 80:
        return "Strong", "green"
    else:
        return "Very Strong", "darkgreen"