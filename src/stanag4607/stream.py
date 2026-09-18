"""Bounded incremental STANAG 4607 packet stream decoding."""

from __future__ import annotations

from .errors import DecodeError
from .packet import PACKET_HEADER_SIZE, DecodeLimits, Packet, decode_packet, decode_packet_header


class PacketStreamDecoder:
    """Reassemble complete packets across arbitrary input chunk boundaries.

    A decoding error places the instance in a failed state. ``reset()`` is
    required before reuse, preventing accidental continuation from an unknown
    byte boundary. ``finish()`` is terminal and reports buffered truncation.
    """

    def __init__(self, *, limits: DecodeLimits | None = None) -> None:
        self._limits = DecodeLimits() if limits is None else limits
        self._buffer = bytearray()
        self._expected_size: int | None = None
        self._failed = False
        self._finished = False

    @property
    def buffered_bytes(self) -> int:
        """Number of incomplete packet bytes retained internally."""

        return len(self._buffer)

    @property
    def failed(self) -> bool:
        """Whether a decode error requires an explicit reset."""

        return self._failed

    def feed(self, data: bytes | bytearray | memoryview) -> tuple[Packet, ...]:
        """Consume a chunk and return all packets completed by that chunk."""

        self._require_active()
        source = memoryview(data).cast("B")
        offset = 0
        packets: list[Packet] = []

        try:
            while offset < len(source):
                if self._expected_size is None:
                    offset = self._fill(source, offset, PACKET_HEADER_SIZE)
                    if len(self._buffer) < PACKET_HEADER_SIZE:
                        break
                    header = decode_packet_header(self._buffer)
                    if header.packet_size > self._limits.max_packet_size:
                        raise DecodeError(
                            f"declared packet size {header.packet_size} exceeds maximum packet "
                            f"size {self._limits.max_packet_size}"
                        )
                    self._expected_size = header.packet_size

                offset = self._fill(source, offset, self._expected_size)
                if len(self._buffer) < self._expected_size:
                    break

                packets.append(decode_packet(self._buffer, limits=self._limits))
                self._buffer.clear()
                self._expected_size = None
        except DecodeError:
            self._failed = True
            raise

        return tuple(packets)

    def finish(self) -> None:
        """Finalize input, rejecting any incomplete packet, and close the decoder."""

        self._require_active()
        self._finished = True
        if not self._buffer:
            return
        if self._expected_size is None:
            raise DecodeError(
                f"truncated packet header: {len(self._buffer)} of {PACKET_HEADER_SIZE} bytes"
            )
        raise DecodeError(
            f"truncated packet: {len(self._buffer)} of {self._expected_size} declared bytes"
        )

    def reset(self) -> None:
        """Discard buffered state and make a failed or finished decoder reusable."""

        self._buffer.clear()
        self._expected_size = None
        self._failed = False
        self._finished = False

    def _fill(self, source: memoryview, offset: int, target_size: int) -> int:
        available = len(source) - offset
        needed = target_size - len(self._buffer)
        take = min(available, needed)
        self._buffer.extend(source[offset : offset + take])
        return offset + take

    def _require_active(self) -> None:
        if self._failed:
            raise RuntimeError("packet stream decoder has failed; call reset() before reuse")
        if self._finished:
            raise RuntimeError("packet stream decoder is finished; call reset() before reuse")

