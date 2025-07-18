# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: tracklab_server.proto
# Protobuf Python Version: 6.31.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# Skip version validation for compatibility

_sym_db = _symbol_database.Default()


from . import tracklab_base_pb2 as tracklab__base__pb2
from . import tracklab_internal_pb2 as tracklab__internal__pb2
from . import tracklab_settings_pb2 as tracklab__settings__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15tracklab_server.proto\x12\x11tracklab_internal\x1a\x13tracklab_base.proto\x1a\x17tracklab_internal.proto\x1a\x17tracklab_settings.proto\"n\n\x19ServerAuthenticateRequest\x12\x0f\n\x07\x61pi_key\x18\x01 \x01(\t\x12\x10\n\x08\x62\x61se_url\x18\x02 \x01(\t\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"z\n\x1aServerAuthenticateResponse\x12\x16\n\x0e\x64\x65\x66\x61ult_entity\x18\x01 \x01(\t\x12\x14\n\x0c\x65rror_status\x18\x02 \x01(\t\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"G\n\x15ServerShutdownRequest\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x18\n\x16ServerShutdownResponse\"E\n\x13ServerStatusRequest\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x16\n\x14ServerStatusResponse\"x\n\x17ServerInformInitRequest\x12-\n\x08settings\x18\x01 \x01(\x0b\x32\x1b.tracklab_internal.Settings\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x1a\n\x18ServerInformInitResponse\"y\n\x18ServerInformStartRequest\x12-\n\x08settings\x18\x01 \x01(\x0b\x32\x1b.tracklab_internal.Settings\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x1b\n\x19ServerInformStartResponse\"K\n\x19ServerInformFinishRequest\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x1c\n\x1aServerInformFinishResponse\"K\n\x19ServerInformAttachRequest\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"{\n\x1aServerInformAttachResponse\x12-\n\x08settings\x18\x01 \x01(\x0b\x32\x1b.tracklab_internal.Settings\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"K\n\x19ServerInformDetachRequest\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x1c\n\x1aServerInformDetachResponse\"`\n\x1bServerInformTeardownRequest\x12\x11\n\texit_code\x18\x01 \x01(\x05\x12.\n\x05_info\x18\xc8\x01 \x01(\x0b\x32\x1e.tracklab_internal._RecordInfo\"\x1e\n\x1cServerInformTeardownResponse\"\x96\x05\n\rServerRequest\x12\x12\n\nrequest_id\x18\n \x01(\t\x12\x33\n\x0erecord_publish\x18\x01 \x01(\x0b\x32\x19.tracklab_internal.RecordH\x00\x12\x37\n\x12record_communicate\x18\x02 \x01(\x0b\x32\x19.tracklab_internal.RecordH\x00\x12\x41\n\x0binform_init\x18\x03 \x01(\x0b\x32*.tracklab_internal.ServerInformInitRequestH\x00\x12\x45\n\rinform_finish\x18\x04 \x01(\x0b\x32,.tracklab_internal.ServerInformFinishRequestH\x00\x12\x45\n\rinform_attach\x18\x05 \x01(\x0b\x32,.tracklab_internal.ServerInformAttachRequestH\x00\x12\x45\n\rinform_detach\x18\x06 \x01(\x0b\x32,.tracklab_internal.ServerInformDetachRequestH\x00\x12I\n\x0finform_teardown\x18\x07 \x01(\x0b\x32..tracklab_internal.ServerInformTeardownRequestH\x00\x12\x43\n\x0cinform_start\x18\x08 \x01(\x0b\x32+.tracklab_internal.ServerInformStartRequestH\x00\x12\x44\n\x0c\x61uthenticate\x18\t \x01(\x0b\x32,.tracklab_internal.ServerAuthenticateRequestH\x00\x42\x15\n\x13server_request_type\"\xa9\x05\n\x0eServerResponse\x12\x12\n\nrequest_id\x18\n \x01(\t\x12\x37\n\x12result_communicate\x18\x02 \x01(\x0b\x32\x19.tracklab_internal.ResultH\x00\x12K\n\x14inform_init_response\x18\x03 \x01(\x0b\x32+.tracklab_internal.ServerInformInitResponseH\x00\x12O\n\x16inform_finish_response\x18\x04 \x01(\x0b\x32-.tracklab_internal.ServerInformFinishResponseH\x00\x12O\n\x16inform_attach_response\x18\x05 \x01(\x0b\x32-.tracklab_internal.ServerInformAttachResponseH\x00\x12O\n\x16inform_detach_response\x18\x06 \x01(\x0b\x32-.tracklab_internal.ServerInformDetachResponseH\x00\x12S\n\x18inform_teardown_response\x18\x07 \x01(\x0b\x32/.tracklab_internal.ServerInformTeardownResponseH\x00\x12M\n\x15inform_start_response\x18\x08 \x01(\x0b\x32,.tracklab_internal.ServerInformStartResponseH\x00\x12N\n\x15\x61uthenticate_response\x18\t \x01(\x0b\x32-.tracklab_internal.ServerAuthenticateResponseH\x00\x42\x16\n\x14server_response_typeB\x1bZ\x19\x63ore/pkg/service_go_protob\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'tracklab_server_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\031core/pkg/service_go_proto'
  _globals['_SERVERAUTHENTICATEREQUEST']._serialized_start=115
  _globals['_SERVERAUTHENTICATEREQUEST']._serialized_end=225
  _globals['_SERVERAUTHENTICATERESPONSE']._serialized_start=227
  _globals['_SERVERAUTHENTICATERESPONSE']._serialized_end=349
  _globals['_SERVERSHUTDOWNREQUEST']._serialized_start=351
  _globals['_SERVERSHUTDOWNREQUEST']._serialized_end=422
  _globals['_SERVERSHUTDOWNRESPONSE']._serialized_start=424
  _globals['_SERVERSHUTDOWNRESPONSE']._serialized_end=448
  _globals['_SERVERSTATUSREQUEST']._serialized_start=450
  _globals['_SERVERSTATUSREQUEST']._serialized_end=519
  _globals['_SERVERSTATUSRESPONSE']._serialized_start=521
  _globals['_SERVERSTATUSRESPONSE']._serialized_end=543
  _globals['_SERVERINFORMINITREQUEST']._serialized_start=545
  _globals['_SERVERINFORMINITREQUEST']._serialized_end=665
  _globals['_SERVERINFORMINITRESPONSE']._serialized_start=667
  _globals['_SERVERINFORMINITRESPONSE']._serialized_end=693
  _globals['_SERVERINFORMSTARTREQUEST']._serialized_start=695
  _globals['_SERVERINFORMSTARTREQUEST']._serialized_end=816
  _globals['_SERVERINFORMSTARTRESPONSE']._serialized_start=818
  _globals['_SERVERINFORMSTARTRESPONSE']._serialized_end=845
  _globals['_SERVERINFORMFINISHREQUEST']._serialized_start=847
  _globals['_SERVERINFORMFINISHREQUEST']._serialized_end=922
  _globals['_SERVERINFORMFINISHRESPONSE']._serialized_start=924
  _globals['_SERVERINFORMFINISHRESPONSE']._serialized_end=952
  _globals['_SERVERINFORMATTACHREQUEST']._serialized_start=954
  _globals['_SERVERINFORMATTACHREQUEST']._serialized_end=1029
  _globals['_SERVERINFORMATTACHRESPONSE']._serialized_start=1031
  _globals['_SERVERINFORMATTACHRESPONSE']._serialized_end=1154
  _globals['_SERVERINFORMDETACHREQUEST']._serialized_start=1156
  _globals['_SERVERINFORMDETACHREQUEST']._serialized_end=1231
  _globals['_SERVERINFORMDETACHRESPONSE']._serialized_start=1233
  _globals['_SERVERINFORMDETACHRESPONSE']._serialized_end=1261
  _globals['_SERVERINFORMTEARDOWNREQUEST']._serialized_start=1263
  _globals['_SERVERINFORMTEARDOWNREQUEST']._serialized_end=1359
  _globals['_SERVERINFORMTEARDOWNRESPONSE']._serialized_start=1361
  _globals['_SERVERINFORMTEARDOWNRESPONSE']._serialized_end=1391
  _globals['_SERVERREQUEST']._serialized_start=1394
  _globals['_SERVERREQUEST']._serialized_end=2056
  _globals['_SERVERRESPONSE']._serialized_start=2059
  _globals['_SERVERRESPONSE']._serialized_end=2740
# @@protoc_insertion_point(module_scope)
