from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BaseRequest(_message.Message):
    __slots__ = ["host_config", "scan_type", "snmp_config"]
    HOST_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SCAN_TYPE_FIELD_NUMBER: _ClassVar[int]
    SNMP_CONFIG_FIELD_NUMBER: _ClassVar[int]
    host_config: HostConfig
    scan_type: str
    snmp_config: SNMPConfig
    def __init__(self, scan_type: _Optional[str] = ..., host_config: _Optional[_Union[HostConfig, _Mapping]] = ..., snmp_config: _Optional[_Union[SNMPConfig, _Mapping]] = ...) -> None: ...

class DiscoverRequest(_message.Message):
    __slots__ = ["nmap_config", "snmp_config", "update_dynamic"]
    NMAP_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SNMP_CONFIG_FIELD_NUMBER: _ClassVar[int]
    UPDATE_DYNAMIC_FIELD_NUMBER: _ClassVar[int]
    nmap_config: ScanNMAPConfig
    snmp_config: ScanSNMPConfig
    update_dynamic: bool
    def __init__(self, update_dynamic: bool = ..., nmap_config: _Optional[_Union[ScanNMAPConfig, _Mapping]] = ..., snmp_config: _Optional[_Union[ScanSNMPConfig, _Mapping]] = ...) -> None: ...

class HostConfig(_message.Message):
    __slots__ = ["host", "port"]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class Rapid7Request(_message.Message):
    __slots__ = ["api_password", "api_url", "api_user", "host", "port", "site_regex"]
    API_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    API_URL_FIELD_NUMBER: _ClassVar[int]
    API_USER_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SITE_REGEX_FIELD_NUMBER: _ClassVar[int]
    api_password: str
    api_url: str
    api_user: str
    host: str
    port: int
    site_regex: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., api_url: _Optional[str] = ..., api_user: _Optional[str] = ..., api_password: _Optional[str] = ..., site_regex: _Optional[_Iterable[str]] = ...) -> None: ...

class Rapid7Response(_message.Message):
    __slots__ = ["message", "result", "status"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    message: str
    result: str
    status: bool
    def __init__(self, status: bool = ..., message: _Optional[str] = ..., result: _Optional[str] = ...) -> None: ...

class SNMPConfig(_message.Message):
    __slots__ = ["convert_to_string", "max_repetitions", "oid", "read_community", "version"]
    CONVERT_TO_STRING_FIELD_NUMBER: _ClassVar[int]
    MAX_REPETITIONS_FIELD_NUMBER: _ClassVar[int]
    OID_FIELD_NUMBER: _ClassVar[int]
    READ_COMMUNITY_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    convert_to_string: bool
    max_repetitions: int
    oid: str
    read_community: str
    version: str
    def __init__(self, read_community: _Optional[str] = ..., version: _Optional[str] = ..., max_repetitions: _Optional[int] = ..., convert_to_string: bool = ..., oid: _Optional[str] = ...) -> None: ...

class SNMPResponse(_message.Message):
    __slots__ = ["message", "result", "status"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    message: str
    result: str
    status: bool
    def __init__(self, status: bool = ..., message: _Optional[str] = ..., result: _Optional[str] = ...) -> None: ...

class ScanNMAPConfig(_message.Message):
    __slots__ = ["network", "port", "scan_spend"]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SCAN_SPEND_FIELD_NUMBER: _ClassVar[int]
    network: _containers.RepeatedScalarFieldContainer[str]
    port: int
    scan_spend: str
    def __init__(self, network: _Optional[_Iterable[str]] = ..., port: _Optional[int] = ..., scan_spend: _Optional[str] = ...) -> None: ...

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

class ScanSNMPConfig(_message.Message):
    __slots__ = ["convert_to_string", "max_repetitions", "oid", "read_community", "version"]
    CONVERT_TO_STRING_FIELD_NUMBER: _ClassVar[int]
    MAX_REPETITIONS_FIELD_NUMBER: _ClassVar[int]
    OID_FIELD_NUMBER: _ClassVar[int]
    READ_COMMUNITY_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    convert_to_string: bool
    max_repetitions: int
    oid: str
    read_community: _containers.RepeatedScalarFieldContainer[str]
    version: str
    def __init__(self, read_community: _Optional[_Iterable[str]] = ..., version: _Optional[str] = ..., max_repetitions: _Optional[int] = ..., convert_to_string: bool = ..., oid: _Optional[str] = ...) -> None: ...
