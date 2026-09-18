# Test fixture provenance

`mission_dwell_hi_res_targets.gmti` is an unchanged 254-byte synthetic STANAG
4607 Version ID `41` packet from the Apache-2.0-licensed
[`Decent-Cybersecurity/synapsecommand-public`](https://github.com/Decent-Cybersecurity/synapsecommand-public)
fixture corpus. SHA-256:
`cb170e15208b8b16add227fbc3c55e32d27f433d9dfbe1a4bddefe549c6b3953`.

It is independent interoperability evidence, not a normative or official vector,
and not operational radar data. See `THIRD_PARTY_NOTICES.md`.

`full_mask_every_optional_group.gmti` is an unchanged 286-byte packet from the
same source. It exercises every compatible optional Dwell/Target field group and
has SHA-256
`a014df23ce8d2146192561d09614f8a24dd60a7acf91cf8cf2a2431d0f75e7f6`.

The following unchanged packets come from the same repository and pinned revision
recorded in `references/data/manifest.json`:

| Fixture | SHA-256 | Evidence exercised |
|---|---|---|
| `free_text_and_test_status.gmti` | `f3d6182ba005869f2806a8e9ae69e2cd00c21529fc7c0b7a1fe4299bcde2186f` | Free Text, Test and Status, exact UTC |
| `processing_history_chain.gmti` | `feb0589fcbaea97bf8b6c1f822ea1a937f93ae2b6321d70e5d7cdc087ab2d191` | Two-record Processing History |
| `platform_location_mixed_time_basis.gmti` | `94f2ae1a89d4f83df7e501b5106c6a7a1891ec068b52bc0e5fe8453f9ad9b98b` | Dwell and repeated Platform Location times |
| `repeated_mission_segment.gmti` | `4199e3b785fbe272696d39685d7ee6cfdbd51876cd068c7635f8374e7e89aa12` | Repeated Mission context and subsequent UTC |
| `reserved_and_extension_segments_recorded.gmti` | `d7df33dda9e235cd900228fa657769ec7ad6b5ead8de4b69fde69b38e5f9a350` | Opaque reserved and extension preservation |
| `hrr_signature_parked_both_time_branches.gmti` | `1dd187becfab9bd43c6d97b5385eb4f152f0e2ebbffb527a19973b0d78b12c7a` | Typed HRR H1-H31 and uncompressed H32 records |

These are synthetic interoperability fixtures from another implementation. Their
presence raises confidence in framing and the listed typed boundaries but does not
replace normative tests or demonstrate operational radar interoperability.
