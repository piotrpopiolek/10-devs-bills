class AppError(Exception):
    """Base class for all application exceptions."""
    pass

class ResourceNotFoundError(AppError):
    """Generic error when a requested resource is not found."""
    def __init__(self, resource_name: str, identifier: any):
        self.message = f"{resource_name} z identyfikatorem {identifier} nie znaleziono."
        super().__init__(self.message)

class ResourceAlreadyExistsError(AppError):
    def __init__(self, resource_name: str, field: str, value: any):
        self.message = f"{resource_name} z {field} '{value}' już istnieje."
        super().__init__(self.message)