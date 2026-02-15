def password_strength(password):
    score = 0
    length = len(password)

    if length >= 12:
        score += 2
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(not c.isalnum() for c in password):
        score += 1

    return score  # 0–6