from typing import Optional
from src.common.exceptions import AppError


class ProcessingError(AppError):

    def __init__(self, message: str, bill_id: Optional[int] = None):
        self.message = message
        self.bill_id = bill_id
        super().__init__(self.message)

