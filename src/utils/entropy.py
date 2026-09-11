import math
import re
from itertools import pairwise


def _shortest_repeating_unit(value):
    """Return a repeated unit, or ``None`` when the value is not periodic."""
    for size in range(1, len(value) // 2 + 1):
        if len(value) % size == 0 and value == value[:size] * (len(value) // size):
            return value[:size]
    return None


def _is_simple_sequence(value):
    """Recognize obvious ascending or descending character sequences."""
    if len(value) < 3:
        return False
    steps = [ord(right) - ord(left) for left, right in pairwise(value)]
    return all(step == 1 for step in steps) or all(step == -1 for step in steps)

def calculate_entropy(password):
    """
    Estimate an upper bound for a non-generated password's entropy.

    Composition cannot measure a human-chosen password's true entropy.  This
    deliberately penalizes obvious repetitions and sequences so the UI never
    labels them strong merely because they are long.
    """
    if not password:
        return 0

    repeated_unit = _shortest_repeating_unit(password)
    if repeated_unit is not None:
        password = repeated_unit
    if len(set(password)) == 1 or _is_simple_sequence(password):
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
    
    # If no character set detected, default to lowercase.
    if charset_size == 0:
        charset_size = 26
    
    # This remains an upper bound, not a measurement of user-chosen entropy.
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
