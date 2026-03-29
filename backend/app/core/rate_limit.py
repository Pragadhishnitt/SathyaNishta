import time
from typing import Dict, Optional
from fastapi import HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for given identifier

        Args:
            identifier: Unique identifier (IP address, email, user ID, etc.)

        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()

        # Clean old requests
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove requests older than time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] if current_time - req_time < self.time_window
        ]

        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True

        return False

    def get_retry_after(self, identifier: str) -> Optional[int]:
        """
        Get seconds to wait before next request is allowed

        Args:
            identifier: Unique identifier

        Returns:
            Seconds to wait, or None if request is allowed
        """
        if self.is_allowed(identifier):
            return None

        if identifier not in self.requests or not self.requests[identifier]:
            return self.time_window

        # Find the oldest request in the current window
        oldest_request = min(self.requests[identifier])
        retry_after = int(self.time_window - (time.time() - oldest_request))
        return max(1, retry_after)


# Rate limiters for different endpoints
login_limiter = RateLimiter(max_requests=5, time_window=300)  # 5 login attempts per 5 minutes
register_limiter = RateLimiter(max_requests=3, time_window=3600)  # 3 registrations per hour
password_reset_limiter = RateLimiter(max_requests=3, time_window=3600)  # 3 password resets per hour
email_limiter = RateLimiter(max_requests=10, time_window=3600)  # 10 emails per hour per user


def check_rate_limit(limiter: RateLimiter, identifier: str, error_message: str = "Rate limit exceeded"):
    """
    Check rate limit and raise HTTPException if exceeded

    Args:
        limiter: RateLimiter instance
        identifier: Unique identifier
        error_message: Custom error message

    Raises:
        HTTPException if rate limit is exceeded
    """
    if not limiter.is_allowed(identifier):
        retry_after = limiter.get_retry_after(identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": error_message, "retry_after": retry_after},
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + retry_after),
            },
        )
