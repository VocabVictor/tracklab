import google.protobuf

protobuf_version = google.protobuf.__version__[0]

if protobuf_version == "3":
    from tracklab.proto.v3.tracklab_telemetry_pb2 import *
elif protobuf_version == "4":
    from tracklab.proto.v4.tracklab_telemetry_pb2 import *
elif protobuf_version == "5":
    from tracklab.proto.v5.tracklab_telemetry_pb2 import *
elif protobuf_version == "6":
    from tracklab.proto.v6.tracklab_telemetry_pb2 import *
