# DMM-SimQA defect reports

SIMQA-101 was observed during integration. SIMQA-102 and SIMQA-103 are controlled fault-injection reports. Each injected change was exercised in a temporary source copy to verify that its regression test detects the failure.

| Field | SIMQA-101 |
| --- | --- |
| Bug ID | SIMQA-101 |
| Summary | Server shutdown hangs while an idle client remains connected |
| Severity | Critical |
| Priority | P0 |
| Environment | Windows, Python 3.12.1, loopback TCP, thread-per-connection listener |
| Steps to Reproduce | Start on port zero, connect, query OUTP?, then call stop() before closing the client. |
| Expected Result | The listener releases the port and joins its connection workers. |
| Actual Result | A thread dump after five seconds showed the worker in socket read and the caller waiting in server_close(). |
| Root Cause | The original worker used a blocking buffered read. Shutting down the peer socket from another thread did not release that read on the verification host. |
| Resolution/Status | Resolved. Workers retain partial frames across bounded receive waits and check a stop event. Verified by test_stop_idle_peer. |

| Field | SIMQA-102 |
| --- | --- |
| Bug ID | SIMQA-102 |
| Summary | Premature display rounding hides a reduced-range overload |
| Severity | Major |
| Priority | P1 |
| Environment | Temporary source copy, Windows, Python 3.12.1, seeded noise |
| Steps to Reproduce | In the fault variant compare the rounded input to full scale. Select 0.1 V range, enable output, inject 0.10001 V and measure DC voltage. |
| Expected Result | Return 9.9E+37 and queue -222. |
| Actual Result | The variant rounded the comparison input to 0.100 V and reported a noisy 0.092 V reading. |
| Root Cause | Quantization erased the overrange condition before validation. |
| Resolution/Status | Resolved in the delivered model. Compare the raw signal first. The reduced-range test_overload parameter fails against the variant and passes against the delivered code. |

| Field | SIMQA-103 |
| --- | --- |
| Bug ID | SIMQA-103 |
| Summary | Instrument reset leaves a stale command error |
| Severity | Major |
| Priority | P1 |
| Environment | Temporary source copy, Windows, Python 3.12.1, fresh in-process parser |
| Steps to Reproduce | In the fault variant omit the FIFO clear during reset. Send BAD, then *RST, then SYST:ERR?. |
| Expected Result | Return 0,"No error". |
| Actual Result | Returned -100,"Command error" after reset. |
| Root Cause | Reset restored measurement settings but retained diagnostics from the previous session. |
| Resolution/Status | Resolved in the delivered model. Reset clears the existing queue. Verified by test_reset_defaults against both implementations. |
