import google.protobuf

protobuf_version = google.protobuf.__version__[0]

if protobuf_version == "3":
    from tracklab.proto.v3.wandb_internal_pb2 import *
elif protobuf_version == "4":
    from tracklab.proto.v4.wandb_internal_pb2 import *
elif protobuf_version == "5":
    from tracklab.proto.v5.wandb_internal_pb2 import *
elif protobuf_version == "6":
    from tracklab.proto.v6.wandb_internal_pb2 import *
else:
    raise ImportError(
        "Failed to import protobufs for protobuf version"
        f" {google.protobuf.__version__}. `wandb` only works with major"
        " versions 3, 4, 5, and 6 of the protobuf package.",
    )
