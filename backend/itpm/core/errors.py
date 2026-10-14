class AppError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = 'VALIDATION_ERROR', field: str = 'error',safe_details=None,request_id=''):
        super().__init__(message)
        self.message, self.status, self.code, self.field = message, status, code, field
        self.safe_details,self.request_id=safe_details or {},request_id


def require(condition, message, status=400, code='VALIDATION_ERROR'):
    if not condition:
        raise AppError(message, status, code)
