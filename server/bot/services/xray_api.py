"""
Dem1chVPN — gRPC клиент к Xray
"""
import asyncio
import logging
from typing import Optional

import grpc
from google.protobuf import json_format

from ..config import config

logger = logging.getLogger("dem1chvpn.xray_api")


class XrayAPI:


    def __init__(self):
        self.address = f"{config.XRAY_API_HOST}:{config.XRAY_API_PORT}"

    def _get_channel(self):

        return grpc.insecure_channel(self.address)

    async def get_user_traffic(self, email: str, reset: bool = False) -> dict:

        uplink = await self._query_stats(f"user>>>{email}>>>traffic>>>uplink", reset)
        downlink = await self._query_stats(f"user>>>{email}>>>traffic>>>downlink", reset)
        return {"uplink": uplink, "downlink": downlink}

    async def get_inbound_traffic(self, tag: str = "vless-reality") -> dict:

        uplink = await self._query_stats(f"inbound>>>{tag}>>>traffic>>>uplink", False)
        downlink = await self._query_stats(f"inbound>>>{tag}>>>traffic>>>downlink", False)
        return {"uplink": uplink, "downlink": downlink}

    async def get_outbound_traffic(self, tag: str = "direct") -> dict:

        uplink = await self._query_stats(f"outbound>>>{tag}>>>traffic>>>uplink", False)
        downlink = await self._query_stats(f"outbound>>>{tag}>>>traffic>>>downlink", False)
        return {"uplink": uplink, "downlink": downlink}

    async def get_all_user_stats(self, reset: bool = False) -> dict:

        users = {}
        try:
            stats = await self._query_all_stats(reset)
            for stat in stats:
                name = stat.get("name", "")
                value = stat.get("value", 0)
                if name.startswith("user>>>"):
                    parts = name.split(">>>")
                    if len(parts) == 4:
                        email = parts[1]
                        direction = parts[3]
                        if email not in users:
                            users[email] = {"uplink": 0, "downlink": 0}
                        users[email][direction] = value
        except Exception as e:
            logger.error(f"Failed to get all user stats: {e}")
        return users

    async def get_sys_stats(self) -> dict:

        try:
            return await self._call_sys_stats()
        except Exception as e:
            logger.error(f"Failed to get sys stats: {e}")
            return {}

    async def _query_stats(self, name: str, reset: bool = False) -> int:

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, self._sync_query_stats, name, reset
            )
        except Exception as e:
            logger.debug(f"Stats query failed for {name}: {e}")
            return 0

    async def _query_all_stats(self, reset: bool = False) -> list:

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, self._sync_query_all_stats, reset
            )
        except Exception as e:
            logger.error(f"All stats query failed: {e}")
            return []

    async def _call_sys_stats(self) -> dict:

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._sync_sys_stats)
        except Exception as e:
            logger.error(f"Sys stats query failed: {e}")
            return {}



    def _sync_query_stats(self, name: str, reset: bool) -> int:

        channel = grpc.insecure_channel(self.address)
        try:
            stub = _StatsServiceStub(channel)
            response = stub.GetStats(
                _GetStatsRequest(name=name, reset=reset),
                timeout=5,
            )
            return response.stat.value if response.stat else 0
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.NOT_FOUND:
                logger.debug(f"gRPC error for {name}: {e.details()}")
            return 0
        except Exception as e:
            logger.debug(f"Stats error: {e}")
            return 0
        finally:
            channel.close()

    def _sync_query_all_stats(self, reset: bool) -> list:

        channel = grpc.insecure_channel(self.address)
        try:
            stub = _StatsServiceStub(channel)
            response = stub.QueryStats(
                _QueryStatsRequest(pattern="", reset=reset),
                timeout=10,
            )
            return [{"name": s.name, "value": s.value} for s in response.stat]
        except Exception as e:
            logger.debug(f"All stats error: {e}")
            return []
        finally:
            channel.close()

    def _sync_sys_stats(self) -> dict:

        channel = grpc.insecure_channel(self.address)
        try:
            stub = _StatsServiceStub(channel)
            response = stub.GetSysStats(_SysStatsRequest(), timeout=5)
            return {
                "num_goroutine": response.NumGoroutine,
                "num_gc": response.NumGC,
                "alloc": response.Alloc,
                "total_alloc": response.TotalAlloc,
                "sys": response.Sys,
                "mallocs": response.Mallocs,
                "frees": response.Frees,
                "live_objects": response.LiveObjects,
                "uptime": response.Uptime,
            }
        except Exception as e:
            logger.debug(f"Sys stats error: {e}")
            return {}
        finally:
            channel.close()




from dataclasses import dataclass, field as dc_field


@dataclass
class _Stat:
    name: str = ""
    value: int = 0


@dataclass
class _GetStatsResponse:
    stat: Optional[_Stat] = None


@dataclass
class _QueryStatsResponse:
    stat: list = dc_field(default_factory=list)


@dataclass
class _SysStatsResponse:
    NumGoroutine: int = 0
    NumGC: int = 0
    Alloc: int = 0
    TotalAlloc: int = 0
    Sys: int = 0
    Mallocs: int = 0
    Frees: int = 0
    LiveObjects: int = 0
    Uptime: int = 0


class _GetStatsRequest:
    def __init__(self, name: str = "", reset: bool = False):
        self.name = name
        self.reset = reset

    def SerializeToString(self):
        result = b""
        if self.name:
            name_bytes = self.name.encode("utf-8")
            result += b"\x0a" + _encode_varint(len(name_bytes)) + name_bytes
        if self.reset:
            result += b"\x10\x01"
        return result


class _QueryStatsRequest:
    def __init__(self, pattern: str = "", reset: bool = False):
        self.pattern = pattern
        self.reset = reset

    def SerializeToString(self):
        result = b""
        if self.pattern:
            p_bytes = self.pattern.encode("utf-8")
            result += b"\x0a" + _encode_varint(len(p_bytes)) + p_bytes
        if self.reset:
            result += b"\x10\x01"
        return result


class _SysStatsRequest:
    def SerializeToString(self):
        return b""


def _encode_varint(value: int) -> bytes:

    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:

    value = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return value, pos


def _varint_to_signed64(value: int) -> int:

    if value >= (1 << 63):
        value -= (1 << 64)
    return value


def _deserialize_stat(data: bytes) -> _Stat:

    stat = _Stat()
    i = 0
    while i < len(data):
        tag = data[i]
        i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 2:
            length, i = _decode_varint(data, i)
            if field_num == 1:
                stat.name = data[i:i + length].decode("utf-8")
            i += length
        elif wire_type == 0:
            value, i = _decode_varint(data, i)
            if field_num == 2:
                stat.value = _varint_to_signed64(value)
        else:
            break
    return stat


def _deserialize_get_stats_response(data: bytes) -> _GetStatsResponse:

    resp = _GetStatsResponse()
    i = 0
    while i < len(data):
        if i >= len(data):
            break
        tag = data[i]
        i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 2 and field_num == 1:
            length, i = _decode_varint(data, i)
            resp.stat = _deserialize_stat(data[i:i + length])
            i += length
        else:
            break
    return resp


def _deserialize_query_stats_response(data: bytes) -> _QueryStatsResponse:

    resp = _QueryStatsResponse()
    i = 0
    while i < len(data):
        if i >= len(data):
            break
        tag = data[i]
        i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 2 and field_num == 1:
            pass
            length = 0
            shift = 0
            while i < len(data):
                b = data[i]
                i += 1
                length |= (b & 0x7F) << shift
                shift += 7
                if not (b & 0x80):
                    break
            stat = _deserialize_stat(data[i:i + length])
            resp.stat.append(stat)
            i += length
        else:
            break
    return resp


def _deserialize_sys_stats_response(data: bytes) -> _SysStatsResponse:

    resp = _SysStatsResponse()
    i = 0
    field_map = {
        1: "NumGoroutine", 2: "NumGC", 3: "Alloc", 4: "TotalAlloc",
        5: "Sys", 6: "Mallocs", 7: "Frees", 8: "LiveObjects", 9: "Uptime",
    }
    while i < len(data):
        if i >= len(data):
            break
        tag = data[i]
        i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:
            value = 0
            shift = 0
            while i < len(data):
                b = data[i]
                i += 1
                value |= (b & 0x7F) << shift
                shift += 7
                if not (b & 0x80):
                    break
            attr = field_map.get(field_num)
            if attr:
                setattr(resp, attr, value)
        else:
            break
    return resp


class _StatsServiceStub:


    SERVICE = "xray.app.stats.command.StatsService"

    def __init__(self, channel):
        self._channel = channel

    def GetStats(self, request, timeout=5):
        response = self._channel.unary_unary(
            f"/{self.SERVICE}/GetStats",
            request_serializer=lambda r: r.SerializeToString(),
            response_deserializer=_deserialize_get_stats_response,
        )(request, timeout=timeout)
        return response

    def QueryStats(self, request, timeout=10):
        response = self._channel.unary_unary(
            f"/{self.SERVICE}/QueryStats",
            request_serializer=lambda r: r.SerializeToString(),
            response_deserializer=_deserialize_query_stats_response,
        )(request, timeout=timeout)
        return response

    def GetSysStats(self, request, timeout=5):
        response = self._channel.unary_unary(
            f"/{self.SERVICE}/GetSysStats",
            request_serializer=lambda r: r.SerializeToString(),
            response_deserializer=_deserialize_sys_stats_response,
        )(request, timeout=timeout)
        return response
