"""Pure-Python building blocks for STANAG 4607 GMTI data.

Protocol behavior is added from authoritative standards through
requirement-linked TDD.
"""

from .angles import BinaryAngle, SignedBinaryAngle
from .binary_decimals import SignedBinaryDecimal, SignedHertzDecimal
from .context import (
    DEFAULT_MAX_JOB_CONTEXTS,
    DEFAULT_MAX_MISSION_CONTEXTS,
    ContextualSegmentEvent,
    ContextualStreamDecoder,
    ContextUpdate,
)
from .continuity import DEFAULT_MAX_CONTINUITY_JOBS, StreamContinuityValidator
from .dwell import (
    DEFAULT_MAX_TARGET_REPORTS,
    DWELL_SEGMENT_TYPE,
    DwellExistenceMask,
    DwellSegment,
    TargetLocation,
    TargetReport,
    decode_dwell_segment,
)
from .errors import DecodeError
from .events import DecodedSegment, SegmentEvent, decode_typed_segment, iter_packet_events
from .free_text import (
    FREE_TEXT_MAX_PAYLOAD_SIZE,
    FREE_TEXT_MIN_PAYLOAD_SIZE,
    FREE_TEXT_PREFIX_SIZE,
    FREE_TEXT_SEGMENT_TYPE,
    FreeTextSegment,
    decode_free_text_segment,
)
from .geojson import dwell_to_geojson
from .hrr import (
    DEFAULT_MAX_HRR_SCATTERER_BYTES,
    HRR_SEGMENT_TYPE,
    HrrExistenceMask,
    HrrScattererRecord,
    HrrSegment,
    decode_hrr_segment,
)
from .job_definition import (
    JOB_DEFINITION_PAYLOAD_SIZE,
    JOB_DEFINITION_SEGMENT_TYPE,
    JobDefinitionSegment,
    decode_job_definition_segment,
)
from .mission import (
    MISSION_PAYLOAD_SIZE,
    MISSION_SEGMENT_TYPE,
    MissionSegment,
    decode_mission_segment,
)
from .packet import (
    DEFAULT_MAX_PACKET_SIZE,
    DEFAULT_MAX_SEGMENTS,
    PACKET_HEADER_SIZE,
    SEGMENT_HEADER_SIZE,
    DecodeLimits,
    Packet,
    PacketHeader,
    Segment,
    SegmentHeader,
    decode_packet,
    decode_packet_header,
    decode_segment_header,
)
from .platform_location import (
    PLATFORM_LOCATION_PAYLOAD_SIZE,
    PLATFORM_LOCATION_SEGMENT_TYPE,
    PlatformLocationSegment,
    decode_platform_location_segment,
)
from .processing_history import (
    PROCESSING_HISTORY_PREFIX_SIZE,
    PROCESSING_HISTORY_SEGMENT_TYPE,
    PROCESSING_RECORD_SIZE,
    ProcessingHistorySegment,
    ProcessingRecord,
    decode_processing_history_segment,
)
from .stream import PacketStreamDecoder
from .tasking import (
    JOB_ACKNOWLEDGE_SEGMENT_TYPE,
    JOB_REQUEST_SEGMENT_TYPE,
    TASKING_PAYLOAD_SIZE,
    JobAcknowledgeSegment,
    JobRequestSegment,
    decode_job_acknowledge_segment,
    decode_job_request_segment,
)
from .test_status import (
    TEST_STATUS_PAYLOAD_SIZE,
    TEST_STATUS_SEGMENT_TYPE,
    TestStatusSegment,
    decode_test_status_segment,
)
from .validation import (
    PacketContextProfile,
    ValidationIssue,
    validate_dwell,
    validate_free_text,
    validate_hrr,
    validate_job_acknowledge,
    validate_job_definition,
    validate_job_request,
    validate_mission,
    validate_packet_context,
    validate_packet_header,
    validate_platform_location,
    validate_processing_history,
    validate_test_status,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_MAX_CONTINUITY_JOBS",
    "DEFAULT_MAX_HRR_SCATTERER_BYTES",
    "DEFAULT_MAX_JOB_CONTEXTS",
    "DEFAULT_MAX_MISSION_CONTEXTS",
    "DEFAULT_MAX_PACKET_SIZE",
    "DEFAULT_MAX_SEGMENTS",
    "DEFAULT_MAX_TARGET_REPORTS",
    "DWELL_SEGMENT_TYPE",
    "FREE_TEXT_MAX_PAYLOAD_SIZE",
    "FREE_TEXT_MIN_PAYLOAD_SIZE",
    "FREE_TEXT_PREFIX_SIZE",
    "FREE_TEXT_SEGMENT_TYPE",
    "HRR_SEGMENT_TYPE",
    "JOB_ACKNOWLEDGE_SEGMENT_TYPE",
    "JOB_DEFINITION_PAYLOAD_SIZE",
    "JOB_DEFINITION_SEGMENT_TYPE",
    "JOB_REQUEST_SEGMENT_TYPE",
    "MISSION_PAYLOAD_SIZE",
    "MISSION_SEGMENT_TYPE",
    "PACKET_HEADER_SIZE",
    "PLATFORM_LOCATION_PAYLOAD_SIZE",
    "PLATFORM_LOCATION_SEGMENT_TYPE",
    "PROCESSING_HISTORY_PREFIX_SIZE",
    "PROCESSING_HISTORY_SEGMENT_TYPE",
    "PROCESSING_RECORD_SIZE",
    "SEGMENT_HEADER_SIZE",
    "TASKING_PAYLOAD_SIZE",
    "TEST_STATUS_PAYLOAD_SIZE",
    "TEST_STATUS_SEGMENT_TYPE",
    "BinaryAngle",
    "ContextUpdate",
    "ContextualSegmentEvent",
    "ContextualStreamDecoder",
    "DecodeError",
    "DecodeLimits",
    "DecodedSegment",
    "DwellExistenceMask",
    "DwellSegment",
    "FreeTextSegment",
    "HrrExistenceMask",
    "HrrScattererRecord",
    "HrrSegment",
    "JobAcknowledgeSegment",
    "JobDefinitionSegment",
    "JobRequestSegment",
    "MissionSegment",
    "Packet",
    "PacketContextProfile",
    "PacketHeader",
    "PacketStreamDecoder",
    "PlatformLocationSegment",
    "ProcessingHistorySegment",
    "ProcessingRecord",
    "Segment",
    "SegmentEvent",
    "SegmentHeader",
    "SignedBinaryAngle",
    "SignedBinaryDecimal",
    "SignedHertzDecimal",
    "StreamContinuityValidator",
    "TargetLocation",
    "TargetReport",
    "TestStatusSegment",
    "ValidationIssue",
    "__version__",
    "decode_dwell_segment",
    "decode_free_text_segment",
    "decode_hrr_segment",
    "decode_job_acknowledge_segment",
    "decode_job_definition_segment",
    "decode_job_request_segment",
    "decode_mission_segment",
    "decode_packet",
    "decode_packet_header",
    "decode_platform_location_segment",
    "decode_processing_history_segment",
    "decode_segment_header",
    "decode_test_status_segment",
    "decode_typed_segment",
    "dwell_to_geojson",
    "iter_packet_events",
    "validate_dwell",
    "validate_free_text",
    "validate_hrr",
    "validate_job_acknowledge",
    "validate_job_definition",
    "validate_job_request",
    "validate_mission",
    "validate_packet_context",
    "validate_packet_header",
    "validate_platform_location",
    "validate_processing_history",
    "validate_test_status",
]
