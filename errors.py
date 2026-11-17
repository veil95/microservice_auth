class UserAlreadyExists(Exception):
    """User already exists"""
    status_code = 409


class ChatServiceUnavailable(Exception):
    """chat-service не ответил"""
    status_code = 503


class RateLimiterUnavailable(Exception):
    status_code = 503
