import pytest
from tracklab.errors import Error
from tracklab.errors.util import ProtobufErrorHandler, ErrorInfo, ErrorCode


@pytest.mark.parametrize(
    "error, expected",
    [
        (ErrorInfo(code=ErrorCode.UNKNOWN, message=""), type(None)),
        (ErrorInfo(code=ErrorCode.COMMUNICATION, message="test error"), Error),
    ],
)
def test_protobuf_error_handler(error, expected):
    exc = ProtobufErrorHandler.to_exception(error)
    assert isinstance(exc, expected)


def test_protobuf_error_handler_exception():
    with pytest.raises(TypeError):
        ProtobufErrorHandler.from_exception(Exception(""))  # type: ignore
