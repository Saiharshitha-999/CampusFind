from difflib import SequenceMatcher
from datetime import datetime
from app.core.config import settings

def score_match(a, b):
    category = 1.0 if a.category.casefold() == b.category.casefold() else 0.0
    desc = SequenceMatcher(None, a.description.casefold(), b.description.casefold()).ratio()
    location = SequenceMatcher(None, a.location.casefold(), b.location.casefold()).ratio()
    try:
        t1 = a.occurred_at.replace(tzinfo=None); t2 = b.occurred_at.replace(tzinfo=None)
        date = max(0, 1 - abs((t1-t2).total_seconds()) / (30*86400))
    except Exception: date = 0
    score = round((category*.4 + desc*.3 + location*.2 + date*.1)*100)
    return {'score':score, 'confidence':'High' if score >= settings.match_high_threshold else 'Medium' if score >= settings.match_medium_threshold else 'Low'}
