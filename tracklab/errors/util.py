from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from . import AuthenticationError, CommError, Error, UnsupportedError, UsageError


class ErrorCode(Enum):
    """Error codes (replacing protobuf enum)."""
    UNKNOWN = "UNKNOWN"
    COMMUNICATION = "COMMUNICATION"
    AUTHENTICATION = "AUTHENTICATION"
    USAGE = "USAGE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass
class ErrorInfo:
    """Error information (replacing protobuf ErrorInfo)."""
    code: ErrorCode
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code.value,
            "message": self.message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorInfo":
        """Create from dictionary."""
        return cls(
            code=ErrorCode(data.get("code", "UNKNOWN")),
            message=data.get("message", "")
        )


to_exception_map = {
    ErrorCode.UNKNOWN: Error,
    ErrorCode.COMMUNICATION: CommError,
    ErrorCode.AUTHENTICATION: AuthenticationError,
    ErrorCode.USAGE: UsageError,
    ErrorCode.UNSUPPORTED: UnsupportedError,
}

from_exception_map = {v: k for k, v in to_exception_map.items()}


class ProtobufErrorHandler:
    """Converts errors to exceptions and vice versa."""

    @staticmethod
    def to_exception(error: ErrorInfo) -> Optional[Error]:
        """Convert an error to an exception.

        Args:
            error: The error to convert.

        Returns:
            The corresponding exception.

        """
        if not error.message:
            return None

        if error.code in to_exception_map:
            return to_exception_map[error.code](error.message)
        return Error(error.message)

    @classmethod
    def from_exception(cls, exc: Error) -> ErrorInfo:
        """Convert a tracklab error to an error message.

        Args:
            exc: The exception to convert.

        Returns:
            The corresponding error message.
        """
        if not isinstance(exc, Error):
            raise TypeError("exc must be a subclass of tracklab.errors.Error")

        code = ErrorCode.UNKNOWN
        for subclass in type(exc).__mro__:
            if subclass in from_exception_map:
                code = from_exception_map[subclass]
                break
        return ErrorInfo(code=code, message=str(exc))
