"""
Keling AI JWT Authentication Manager

Handles JWT token generation and caching for Keling AI API authentication.
Tokens are cached and automatically refreshed 5 minutes before expiry.
"""

import time
import jwt
from typing import Optional
from datetime import datetime, timedelta
import threading


class KelingAuthManager:
    """
    JWT token manager for Keling AI API authentication.

    Implements HS256 JWT signing with automatic token refresh and caching.
    Thread-safe implementation for use in async environments.

    Attributes:
        access_key: AccessKey from Keling AI developer platform (used as JWT issuer)
        secret_key: SecretKey from Keling AI developer platform (used for JWT signing)
        token_ttl: Token time-to-live in seconds (default 1800s = 30 minutes)
        refresh_buffer: Time before expiry to refresh token (default 300s = 5 minutes)
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        token_ttl: int = 1800,  # 30 minutes
        refresh_buffer: int = 300  # 5 minutes
    ):
        """
        Initialize Keling authentication manager.

        Args:
            access_key: AccessKey from Keling AI developer platform
            secret_key: SecretKey for JWT signing (HS256 algorithm)
            token_ttl: Token lifetime in seconds (default 1800)
            refresh_buffer: Refresh token N seconds before expiry (default 300)

        Raises:
            ValueError: If access_key or secret_key is empty
        """
        if not access_key or not secret_key:
            raise ValueError("Both access_key and secret_key must be provided")

        self.access_key = access_key
        self.secret_key = secret_key
        self.token_ttl = token_ttl
        self.refresh_buffer = refresh_buffer

        # Thread-safe token cache
        self._lock = threading.Lock()
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[float] = None

    def generate_token(self, ttl_seconds: Optional[int] = None) -> str:
        """
        Generate a new JWT token for Keling AI API authentication.

        Token format follows Keling AI specification:
        - Algorithm: HS256
        - Issuer (iss): AccessKey
        - Expiration (exp): current_time + ttl_seconds
        - Not Before (nbf): current_time - 5 seconds (clock skew tolerance)

        Args:
            ttl_seconds: Token lifetime in seconds (defaults to self.token_ttl)

        Returns:
            JWT token string

        Raises:
            jwt.PyJWTError: If token generation fails
        """
        ttl = ttl_seconds or self.token_ttl
        current_time = int(time.time())

        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }

        payload = {
            "iss": self.access_key,  # Issuer: AccessKey
            "exp": current_time + ttl,  # Expiration time
            "nbf": current_time - 5  # Not before (5s clock skew tolerance)
        }

        token = jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)

        # PyJWT 2.0+ returns string directly, older versions return bytes
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return token

    def get_valid_token(self) -> str:
        """
        Get a valid JWT token, using cache if available and not expired.

        Automatically generates a new token if:
        - No cached token exists
        - Cached token is within refresh_buffer seconds of expiry
        - Cached token has expired

        This method is thread-safe and can be called concurrently.

        Returns:
            Valid JWT token string
        """
        with self._lock:
            current_time = time.time()

            # Check if we need to refresh the token
            should_refresh = (
                self._cached_token is None or
                self._token_expiry is None or
                current_time >= (self._token_expiry - self.refresh_buffer)
            )

            if should_refresh:
                # Generate new token
                self._cached_token = self.generate_token()
                self._token_expiry = time.time() + self.token_ttl

            return self._cached_token

    def invalidate_cache(self):
        """
        Invalidate cached token, forcing generation of new token on next request.

        Useful when receiving 1004 (authentication failed) errors from API,
        indicating the token may have expired or been invalidated.
        """
        with self._lock:
            self._cached_token = None
            self._token_expiry = None

    def get_auth_header(self) -> dict:
        """
        Get Authorization header with valid JWT token.

        Returns:
            Dictionary with Authorization header ready for HTTP requests
            Example: {"Authorization": "Bearer eyJ..."}
        """
        token = self.get_valid_token()
        return {"Authorization": f"Bearer {token}"}

    def is_token_valid(self) -> bool:
        """
        Check if cached token is still valid (not expired or near expiry).

        Returns:
            True if cached token exists and is valid, False otherwise
        """
        with self._lock:
            if self._cached_token is None or self._token_expiry is None:
                return False

            current_time = time.time()
            return current_time < (self._token_expiry - self.refresh_buffer)

    def get_token_info(self) -> dict:
        """
        Get information about current token state (for debugging/monitoring).

        Returns:
            Dictionary with token state information
        """
        with self._lock:
            if self._cached_token is None or self._token_expiry is None:
                return {
                    "has_token": False,
                    "is_valid": False,
                    "expires_in": None,
                    "expires_at": None
                }

            current_time = time.time()
            expires_in = max(0, self._token_expiry - current_time)
            is_valid = expires_in > self.refresh_buffer

            return {
                "has_token": True,
                "is_valid": is_valid,
                "expires_in": expires_in,
                "expires_at": datetime.fromtimestamp(self._token_expiry).isoformat(),
                "should_refresh_at": datetime.fromtimestamp(
                    self._token_expiry - self.refresh_buffer
                ).isoformat()
            }
