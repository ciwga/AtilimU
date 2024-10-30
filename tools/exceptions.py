class LoginError(Exception):
    def __init__(self, message):
        super().__init__(message)


class IPBanned(Exception):
    def __init__(self, message):
        super().__init__(message)


class SaveError(Exception):
    def __init__(self, message):
        super().__init__(message)


class WrongPageError(Exception):
    def __init__(self, message):
        super().__init__(message)


class NoCoursesAvailableError(Exception):
    def __init__(self, message):
        super().__init__(message)


class NotGraduatedError(Exception):
    def __init__(self, message):
        super().__init__(message)
