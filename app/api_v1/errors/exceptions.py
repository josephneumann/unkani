class ValidationError(ValueError):
    pass


class AuthenticationError(ValueError):
    pass


class TokenExpiredError(AuthenticationError):
    pass
