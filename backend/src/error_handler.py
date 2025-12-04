from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.common.exceptions import (
    ResourceNotFoundError, 
    ResourceAlreadyExistsError,
    AppError
)
from src.categories.exceptions import (
    CategoryCycleError, 
    CategoryHasChildrenError
)
from src.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenAlreadyUsedError,
    UserNotFoundError as AuthUserNotFoundError
)

def exception_handler(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI application.
    Translates domain exceptions into HTTP responses.
    """

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(ResourceAlreadyExistsError)
    async def resource_already_exists_handler(request: Request, exc: ResourceAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @app.exception_handler(CategoryCycleError)
    async def category_cycle_handler(request: Request, exc: CategoryCycleError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(CategoryHasChildrenError)
    async def category_has_children_handler(request: Request, exc: CategoryHasChildrenError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(TokenExpiredError)
    async def token_expired_handler(request: Request, exc: TokenExpiredError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(TokenAlreadyUsedError)
    async def token_already_used_handler(request: Request, exc: TokenAlreadyUsedError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(AuthUserNotFoundError)
    async def auth_user_not_found_handler(request: Request, exc: AuthUserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

