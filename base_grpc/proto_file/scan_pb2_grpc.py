# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import base_grpc.proto_file.scan_pb2 as scan__pb2

class ScanServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Scan = channel.unary_stream(
            '/ScanService/Scan',
            request_serializer=scan__pb2.ScanParameter.SerializeToString,
            response_deserializer=scan__pb2.ScanResult.FromString,
        )

class ScanServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Scan(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_ScanServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Scan': grpc.unary_stream_rpc_method_handler(
                    servicer.Scan,
                    request_deserializer=scan__pb2.ScanParameter.FromString,
                    response_serializer=scan__pb2.ScanResult.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ScanService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

 # This class is part of an EXPERIMENTAL API.
class ScanService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Scan(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/ScanService/Scan',
            scan__pb2.ScanParameter.SerializeToString,
            scan__pb2.ScanResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

class SNMPServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Base = channel.unary_unary(
                '/SNMPService/Base',
                request_serializer=scan__pb2.BaseRequest.SerializeToString,
                response_deserializer=scan__pb2.SNMPResponse.FromString,
                )
        self.Discover = channel.unary_unary(
                '/SNMPService/Discover',
                request_serializer=scan__pb2.DiscoverRequest.SerializeToString,
                response_deserializer=scan__pb2.SNMPResponse.FromString,
                )

class SNMPServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Base(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Discover(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_SNMPServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Base': grpc.unary_unary_rpc_method_handler(
                    servicer.Base,
                    request_deserializer=scan__pb2.BaseRequest.FromString,
                    response_serializer=scan__pb2.SNMPResponse.SerializeToString,
            ),
            'Discover': grpc.unary_unary_rpc_method_handler(
                    servicer.Discover,
                    request_deserializer=scan__pb2.DiscoverRequest.FromString,
                    response_serializer=scan__pb2.SNMPResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'SNMPService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

 # This class is part of an EXPERIMENTAL API.
class SNMPService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Base(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/SNMPService/Base',
            scan__pb2.BaseRequest.SerializeToString,
            scan__pb2.SNMPResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Discover(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/SNMPService/Discover',
            scan__pb2.DiscoverRequest.SerializeToString,
            scan__pb2.SNMPResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class Rapid7ServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Base = channel.unary_unary(
                '/Rapid7Service/Base',
                request_serializer=scan__pb2.Rapid7Request.SerializeToString,
                response_deserializer=scan__pb2.Rapid7Response.FromString,
                )


class Rapid7ServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Base(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Rapid7ServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Base': grpc.unary_unary_rpc_method_handler(
                    servicer.Base,
                    request_deserializer=scan__pb2.Rapid7Request.FromString,
                    response_serializer=scan__pb2.Rapid7Response.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Rapid7Service', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Rapid7Service(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Base(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Rapid7Service/Base',
            scan__pb2.Rapid7Request.SerializeToString,
            scan__pb2.Rapid7Response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
