"""
Custom exceptions for the FastAPI application
"""

from fastapi import HTTPException, status


class OneStopRadioException(Exception):
    """Base exception class for OneStopRadio application"""
    pass


class AuthenticationError(OneStopRadioException):
    """Authentication related errors"""
    pass


class AuthorizationError(OneStopRadioException):
    """Authorization related errors"""
    pass


class ValidationError(OneStopRadioException):
    """Data validation errors"""
    pass


# HTTP Exception shortcuts
def http_401_unauthorized(detail: str = "Could not validate credentials"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_403_forbidden(detail: str = "Not enough permissions"):
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def http_404_not_found(detail: str = "Resource not found"):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def http_400_bad_request(detail: str = "Bad request"):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )