# Validation and export

Validation produces structured issues without rewriting the input. Use the
specific validator for a typed segment, or use the
[CLI](../CLI.md#validate) to check a complete stream with continuity.

::: stanag4607.ValidationIssue

::: stanag4607.validate_packet_header

::: stanag4607.validate_packet_context

::: stanag4607.validate_dwell

::: stanag4607.validate_hrr

::: stanag4607.validate_job_definition

::: stanag4607.dwell_to_geojson

The other typed segments also have dedicated `validate_*` functions exported
from `stanag4607`. The [conformance matrix](../CONFORMANCE.md) identifies their
software-verifiable rules and the [limitations](../LIMITATIONS.md) identifies
where producer context is still needed.
