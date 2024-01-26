class LoginError(Exception):
    def __init__(self, message):
        super().__init__(message)


class IPBanned(Exception):
    def __init__(self, message):
        super().__init__(message)
