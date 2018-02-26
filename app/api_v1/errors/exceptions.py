class APIError(Exception):
    """Base error for API exceptions.  Subclass of Exception"""
    pass


class ValidationError(APIError):
    pass


class PreconditionFailedError(APIError):
    """Used with etag"""
    pass


class NotModifiedError(APIError):
    """Used with etag"""
    pass


class BadRequestError(APIError):
    """Raised in context of API when a 400 error is appropriate."""
    pass


class RateLimitError(APIError):
    """Base error for Rate Limit exceptions.  Subclass of APIError"""
    pass


class ValidationError(APIError):
    """Data content or format validation error.  Sublclass of APIError"""
    pass


class AuthenticationError(APIError):
    """Authentication related error.  Subclass of APIError"""
    pass


class TokenAuthError(AuthenticationError):
    """Token authentication error.  Sublclass of AuthenticationError"""
    pass


class TokenExpiredError(TokenAuthError):
    """Token Expired error.  Subclass of Authentication Error"""
    pass


class BasicAuthError(AuthenticationError):
    """Error related to basic auth requests."""
    pass


class ForbiddenError(AuthenticationError):
    """Forbidden authentication related error.  Subclass of AuthenticationError"""
    pass
