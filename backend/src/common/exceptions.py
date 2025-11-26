class AppError(Exception):
    """Base class for all application exceptions."""
    pass

class ResourceNotFoundError(AppError):
    """Generic error when a requested resource is not found."""
    def __init__(self, resource_name: str, identifier: any):
        self.message = f"{resource_name} with identifier {identifier} not found."
        super().__init__(self.message)

class ResourceAlreadyExistsError(AppError):
    """Generic error when a resource already exists (unique constraint)."""
    def __init__(self, resource_name: str, field: str, value: any):
        self.message = f"{resource_name} with {field} '{value}' already exists."
        super().__init__(self.message)