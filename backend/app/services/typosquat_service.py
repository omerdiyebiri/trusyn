import Levenshtein

def generate_typosquats(domain: str):
    """
    Generate common typosquatting variations for a given domain.
    Simplified version focusing on character replacement and addition.
    """
    parts = domain.split('.')
    name = parts[0]
    tld = '.'.join(parts[1:]) if len(parts) > 1 else 'com'
    
    variations = set()
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    
    # 1. Character replacement
    for i in range(len(name)):
        for char in chars:
            if char != name[i]:
                variations.add(f"{name[:i]}{char}{name[i+1:]}.{tld}")
                
    # 2. Character addition
    for i in range(len(name) + 1):
        for char in chars:
            variations.add(f"{name[:i]}{char}{name[i:]}.{tld}")
            
    # 3. Character omission
    for i in range(len(name)):
        variations.add(f"{name[:i]}{name[i+1:]}.{tld}")
        
    # 4. Transposition
    for i in range(len(name) - 1):
        name_list = list(name)
        name_list[i], name_list[i+1] = name_list[i+1], name_list[i]
        variations.add(f"{''.join(name_list)}.{tld}")
        
    return list(variations)

def calculate_similarity(original: str, suspect: str):
    """
    Calculate similarity score using Levenshtein distance.
    Returns a score between 0 and 1.
    """
    distance = Levenshtein.distance(original, suspect)
    max_len = max(len(original), len(suspect))
    if max_len == 0: return 0
    return 1 - (distance / max_len)
