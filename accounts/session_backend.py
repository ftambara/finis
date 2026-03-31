import secrets

from django.contrib.sessions.backends.cached_db import SessionStore as CachedDBStore


class SessionStore(CachedDBStore):
    def _get_new_session_key(self) -> str:
        """
        Generate a cryptographically secure 20-byte session key.
        Using secrets.token_hex(20) returns 40 characters representing the 20 bytes.
        """
        while True:
            session_key = secrets.token_hex(20)
            if not self.exists(session_key):
                return session_key
