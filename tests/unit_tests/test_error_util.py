import pytest
from tracklab.errors import Error
from tracklab.errors.util import ProtobufErrorHandler
from tracklab.proto import tracklab_internal_pb2 as pb


@pytest.mark.parametrize(
    "error, expected",
    [
        (pb.ErrorInfo(), type(None)),
        (pb.ErrorInfo(code=-2), Error),
    ],
)
def test_protobuf_error_handler(error, expected):
    exc = ProtobufErrorHandler.to_exception(error)
    assert isinstance(exc, expected)


def test_protobuf_error_handler_exception():
    with pytest.raises(TypeError):
        ProtobufErrorHandler.from_exception(Exception(""))  # type: ignore
