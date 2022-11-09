from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ScanParameter(_message.Message):
    __slots__ = ["scan_args", "scan_delay", "scan_host_exclude", "scan_host_port", "scan_host_range", "scan_host_timeout", "scan_mod", "scan_speed"]
    SCAN_ARGS_FIELD_NUMBER: _ClassVar[int]
    SCAN_DELAY_FIELD_NUMBER: _ClassVar[int]
    SCAN_HOST_EXCLUDE_FIELD_NUMBER: _ClassVar[int]
    SCAN_HOST_PORT_FIELD_NUMBER: _ClassVar[int]
    SCAN_HOST_RANGE_FIELD_NUMBER: _ClassVar[int]
    SCAN_HOST_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    SCAN_MOD_FIELD_NUMBER: _ClassVar[int]
    SCAN_SPEED_FIELD_NUMBER: _ClassVar[int]
    scan_args: str
    scan_delay: str
    scan_host_exclude: str
    scan_host_port: str
    scan_host_range: str
    scan_host_timeout: str
    scan_mod: str
    scan_speed: str
    def __init__(self, scan_mod: _Optional[str] = ..., scan_host_range: _Optional[str] = ..., scan_host_port: _Optional[str] = ..., scan_host_exclude: _Optional[str] = ..., scan_speed: _Optional[str] = ..., scan_delay: _Optional[str] = ..., scan_host_timeout: _Optional[str] = ..., scan_args: _Optional[str] = ...) -> None: ...

class ScanResult(_message.Message):
    __slots__ = ["ip", "scan_result"]
    IP_FIELD_NUMBER: _ClassVar[int]
    SCAN_RESULT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    scan_result: str
    def __init__(self, ip: _Optional[str] = ..., scan_result: _Optional[str] = ...) -> None: ...
