"""Dependency-free local live-validation demo for STANAG 4607 streams."""

from __future__ import annotations

import html
import json
import time
from collections.abc import Iterable, Iterator
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .continuity import StreamContinuityValidator
from .dwell import DwellSegment
from .events import SegmentEvent, iter_packet_events
from .free_text import FreeTextSegment
from .hrr import HrrSegment
from .job_definition import JobDefinitionSegment
from .mission import MissionSegment
from .platform_location import PlatformLocationSegment
from .processing_history import ProcessingHistorySegment
from .stream import PacketStreamDecoder
from .tasking import JobAcknowledgeSegment, JobRequestSegment
from .test_status import TestStatusSegment
from .validation import (
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

_CHUNK_SIZE = 64 * 1024


def _segment_issues(event: SegmentEvent) -> tuple[ValidationIssue, ...]:
    value = event.value
    if isinstance(value, MissionSegment):
        return validate_mission(value)
    if isinstance(value, DwellSegment):
        return validate_dwell(value)
    if isinstance(value, FreeTextSegment):
        return validate_free_text(value)
    if isinstance(value, HrrSegment):
        return validate_hrr(value)
    if isinstance(value, JobDefinitionSegment):
        return validate_job_definition(value)
    if isinstance(value, PlatformLocationSegment):
        return validate_platform_location(value)
    if isinstance(value, ProcessingHistorySegment):
        return validate_processing_history(value)
    if isinstance(value, TestStatusSegment):
        return validate_test_status(value)
    if isinstance(value, JobRequestSegment):
        return validate_job_request(value)
    if isinstance(value, JobAcknowledgeSegment):
        return validate_job_acknowledge(value)
    return ()


def _target_records(dwell: DwellSegment) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for target_index, target in enumerate(dwell.targets):
        location = dwell.target_location(target_index)
        if location is None:
            continue
        longitude = location.longitude.degrees
        if longitude > 180:
            longitude -= 360
        records.append(
            {
                "target_index": target_index,
                "report_index": target.report_index,
                "classification": target.classification,
                "coordinates": [float(longitude), float(location.latitude.degrees)],
                "radial_velocity_centimeters_per_second": (
                    target.radial_velocity_centimeters_per_second
                ),
            }
        )
    return records


def iter_demo_events(chunks: Iterable[bytes]) -> Iterator[dict[str, object]]:
    """Yield bounded JSON-compatible validation events from arbitrary chunks."""

    decoder = PacketStreamDecoder()
    continuity = StreamContinuityValidator()
    packet_index = 0
    for chunk in chunks:
        for packet in decoder.feed(chunk):
            packet_issues = (
                *validate_packet_header(packet.header),
                *validate_packet_context(packet),
            )
            for event in iter_packet_events(packet):
                issues = [
                    *(packet_issues if event.segment_index == 0 else ()),
                    *continuity.observe(event),
                    *_segment_issues(event),
                ]
                record: dict[str, object] = {
                    "event": "segment",
                    "packet_index": packet_index,
                    "segment_index": event.segment_index,
                    "segment_type": event.segment.segment_type,
                    "decoded_type": type(event.value).__name__,
                    "platform_id": event.packet_header.platform_id.decode(
                        "ascii", errors="replace"
                    ),
                    "mission_id": event.packet_header.mission_id,
                    "job_id": event.packet_header.job_id,
                    "valid": not issues,
                    "issues": [asdict(issue) for issue in issues],
                }
                if isinstance(event.value, DwellSegment):
                    record["target_count"] = event.value.target_report_count
                    record["dwell_time_milliseconds"] = (
                        event.value.dwell_time_milliseconds
                    )
                    record["targets"] = _target_records(event.value)
                yield record
            packet_index += 1
    decoder.finish()


def demo_document(source_name: str) -> str:
    """Return the self-contained demo page without third-party web dependencies."""

    title = html.escape(source_name)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>STANAG 4607 live validation</title>
<style>
:root{{--bg:#081018;--panel:#101c27;--line:#243746;--text:#dbe9f2;--muted:#8fa6b5;
--good:#43d19e;--bad:#ff6b72;--accent:#5ab5ff}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);
font:14px ui-monospace,SFMono-Regular,Menlo,monospace}}
header{{padding:22px 28px;border-bottom:1px solid var(--line);display:flex;
gap:18px;align-items:center}}
h1{{font-size:19px;margin:0}}
.source{{color:var(--muted);overflow:hidden;text-overflow:ellipsis}}
.live{{margin-left:auto;color:var(--good)}}
main{{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:18px;min-height:250px}}
h2{{font-size:14px;margin:0 0 14px;color:var(--muted);text-transform:uppercase;
letter-spacing:.08em}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.metric{{background:#0b151e;padding:14px;border-radius:8px}}
.metric b{{display:block;font-size:24px;margin-top:6px}}
#status.good{{color:var(--good)}}#status.bad{{color:var(--bad)}}
#plot{{width:100%;height:300px;background:#0b151e;border-radius:8px}}
circle{{fill:var(--accent);stroke:#d9f2ff;stroke-width:1.5}}
#timeline{{display:flex;gap:5px;align-items:center;min-height:42px;overflow:hidden}}
.tick{{width:12px;height:30px;border-radius:3px;background:var(--good);flex:none}}
.tick.bad{{background:var(--bad)}}
#feed{{list-style:none;padding:0;margin:0;max-height:300px;overflow:auto}}
#feed li{{padding:9px 0;border-bottom:1px solid var(--line)}}
.error{{color:var(--bad)}}.muted{{color:var(--muted)}}
@media(max-width:800px){{main{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>STANAG 4607 live monitor</h1><span class="source">{title}</span>
<span class="live" id="connection">● connecting</span></header>
<main><section class="panel"><h2>Live validity</h2><div class="metrics">
<div class="metric">State<b id="status">WAIT</b></div>
<div class="metric">Segments<b id="segments">0</b></div>
<div class="metric">Findings<b id="findings">0</b></div></div>
<h2 style="margin-top:22px">Replay timeline</h2><div id="timeline"></div></section>
<section class="panel"><h2>Target positions</h2>
<svg id="plot" viewBox="0 0 600 300"><text x="300" y="150"
text-anchor="middle" fill="#8fa6b5">waiting for located targets</text></svg></section>
<section class="panel" style="grid-column:1/-1"><h2>Activity feed</h2>
<ul id="feed"></ul></section></main>
<script nonce="stanag4607-local-demo">
let segments=0,findings=0;
const feed=document.querySelector('#feed');
const timeline=document.querySelector('#timeline');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}}[c]));
function plot(targets){{
  if(!targets?.length)return;
  const xs=targets.map(t=>t.coordinates[0]);
  const ys=targets.map(t=>t.coordinates[1]);
  const minx=Math.min(...xs),maxx=Math.max(...xs);
  const miny=Math.min(...ys),maxy=Math.max(...ys);
  const dx=maxx-minx||1,dy=maxy-miny||1;
  document.querySelector('#plot').innerHTML=targets.map(t=>{{
    const x=40+(t.coordinates[0]-minx)/dx*520;
    const y=260-(t.coordinates[1]-miny)/dy*220;
    const tip=`target ${{t.report_index}} · ${{t.coordinates.join(', ')}}`;
    return `<circle cx="${{x}}" cy="${{y}}" r="7"><title>${{tip}}</title></circle>`+
      `<text x="${{x+12}}" y="${{y+4}}" fill="#dbe9f2">`+
      `${{esc(t.report_index)}}</text>`;
  }}).join('');
}}
const stream=new EventSource('/events');
stream.onopen=()=>{{document.querySelector('#connection').textContent='● live'}};
stream.onerror=()=>{{document.querySelector('#connection').textContent='● reconnecting'}};
stream.onmessage=e=>{{
  const d=JSON.parse(e.data);
  if(d.event==='replay'){{timeline.innerHTML='';return}}
  segments++;findings+=d.issues.length;
  document.querySelector('#segments').textContent=segments;
  document.querySelector('#findings').textContent=findings;
  const status=document.querySelector('#status');
  status.textContent=d.valid?'VALID':'ISSUES';status.className=d.valid?'good':'bad';
  const tick=document.createElement('span');
  tick.className='tick'+(d.valid?'':' bad');
  tick.title=`packet ${{d.packet_index}}, segment ${{d.segment_index}}: `+
    `${{d.decoded_type}}`;
  timeline.append(tick);
  while(timeline.children.length>60)timeline.firstChild.remove();
  const li=document.createElement('li');
  const result=d.valid?'valid':esc(d.issues.map(x=>x.code).join(', '));
  li.innerHTML=`<b>${{esc(d.decoded_type)}}</b> · packet ${{d.packet_index}} / `+
    `segment ${{d.segment_index}} · <span class="${{d.valid?'muted':'error'}}">`+
    `${{result}}</span>`;
  feed.prepend(li);
  while(feed.children.length>80)feed.lastChild.remove();
  plot(d.targets);
}};
</script></body></html>"""


def _file_chunks(path: Path) -> Iterator[bytes]:
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK_SIZE):
            yield chunk


def serve_demo(
    path: str,
    *,
    host: str = "127.0.0.1",
    port: int = 8768,
    interval: float = 0.5,
) -> None:
    """Serve a local replay UI until interrupted."""

    source = Path(path).resolve(strict=True)
    if not source.is_file():
        raise ValueError(f"not a regular file: {source}")
    if interval < 0:
        raise ValueError("interval must be zero or greater")

    document = demo_document(source.name).encode()

    class DemoHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def _headers(self, content_type: str) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'unsafe-inline'; "
                "script-src 'nonce-stanag4607-local-demo'",
            )

        def do_GET(self) -> None:
            if self.path == "/":
                self.send_response(HTTPStatus.OK)
                self._headers("text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(document)))
                self.end_headers()
                self.wfile.write(document)
                return
            if self.path == "/events":
                self.send_response(HTTPStatus.OK)
                self._headers("text/event-stream; charset=utf-8")
                self.end_headers()
                try:
                    while True:
                        self.wfile.write(b'data: {"event":"replay"}\n\n')
                        self.wfile.flush()
                        for event in iter_demo_events(_file_chunks(source)):
                            payload = json.dumps(event, separators=(",", ":")).encode()
                            self.wfile.write(b"data: " + payload + b"\n\n")
                            self.wfile.flush()
                            if interval:
                                time.sleep(interval)
                except (BrokenPipeError, ConnectionResetError):
                    return
            self.send_error(HTTPStatus.NOT_FOUND)

    server = ThreadingHTTPServer((host, port), DemoHandler)
    try:
        print(f"STANAG 4607 demo: http://{host}:{server.server_port}/")
        server.serve_forever()
    finally:
        server.server_close()
