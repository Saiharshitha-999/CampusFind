import base64, hashlib, hmac, json, time
from app.core.config import settings

def hash_password(password: str) -> str:
    salt = __import__('secrets').token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, digest = encoded.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.urlsafe_b64decode(salt), 310000)
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode(), digest)
    except Exception: return False

def create_token(user_id: int, purpose: str = 'access', ttl: int = 3600) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({'sub': user_id, 'purpose': purpose, 'exp': int(time.time()) + ttl}).encode()).decode().rstrip('=')
    signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f'{payload}.{signature}'

def read_token(token: str, purpose: str = 'access') -> int | None:
    try:
        payload, sig = token.rsplit('.', 1)
        expected = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): return None
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        if data['exp'] < time.time() or data['purpose'] != purpose: return None
        return int(data['sub'])
    except Exception: return None
