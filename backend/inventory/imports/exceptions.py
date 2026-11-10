from rest_framework.exceptions import APIException


class ImportPayloadTooLarge(APIException):
    status_code = 413
    default_detail = "El archivo supera un límite técnico."
    default_code = "import_limit_exceeded"


class ImportDependencyUnavailable(Exception):
    pass


class ImportDomainConflict(Exception):
    pass


class ImportDomainValidation(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(str(detail))
