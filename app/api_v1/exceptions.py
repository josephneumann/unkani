from app.api_v1.errors import AuthenticationError

class TokenExpiredError(AuthenticationError):
    pass