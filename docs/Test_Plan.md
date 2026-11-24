# DMM-SimQA Master Test Plan

## Objective

Qualify the simulator as a repeatable reference instrument for local SCPI client development. A caller must be able to distinguish a valid zero, overload, command error and broken connection using the documented protocol.

## Scope

**In scope** are instrument identity and reset (REQ-STATE), mode and range selection (REQ-CONF), output gating (REQ-GATE), signal, noise and display resolution (REQ-MEAS), boundary classification (REQ-LIMIT), FIFO diagnostics (REQ-ERR), command grammar (REQ-PARSE) and TCP framing, concurrency and lifecycle (REQ-TCP). These identifiers link acceptance checks to the case matrix.

**Out of scope** are hardware calibration, electrical safety certification, GPIB/VISA timing, compound program messages and commands outside the README reference.

## Test strategy

| Level or technique | Stimulus and acceptance oracle |
| --- | --- |
| Smoke | Identify the meter, dirty its state and reset, drain an empty FIFO and exercise both output settings. Compare exact wire strings. |
| Functional and regression | Exercise all three functions and long/short headers. With noise disabled, assert display digits exactly. With noise enabled, sample 400 readings at an interior input using a seeded generator. Compare the sample mean to the input within 0.2 standard deviations and sample deviation to the specification within 15%. |
| Boundary value analysis | Include zero, one display count, exact full scale, one count beyond full scale and negative input. Also exceed a reduced range by less than one count to detect premature rounding. |
| Equivalence partitioning | Partition ranges into nonpositive, valid and above maximum. Partition arguments into valid decimal, scientific notation, non-numeric, missing and excess. Verify rejected configuration retains prior state. |
| Negative | Check the exact error string, FIFO order and recovery. Output off always yields formatted zero and leaves the FIFO unchanged, including an otherwise overrange input. With output enabled a wrong-function query produces -221. |
| Integration | Bind a real loopback server to port zero. Verify fragmented and concatenated lines, shared state across four synchronized clients, partial disconnects, shutdown with an idle client and a timed-out query followed by a healthy session. |

## Test environment

Run from the repository root with Python 3.10+, an isolated environment and the dependencies pinned in requirements.txt. Hosted jobs target Linux and Python 3.11. Local qualification used Windows and Python 3.12.1. Each parser case starts with a fresh meter. Transport cases share a module-scoped listener and synchronize reset with a query before each client fixture yields.

## Entry and exit criteria

Entry requires importable source, installed QA plugins, writable reports directory and an available loopback socket. Run `python -m pytest` for release evidence. Review failed nodes individually, then rerun the full suite after any correction.

Exit requires all collected tests passing, zero warnings, at least 90% aggregate statement coverage, a readable self-contained HTML report, complete case mappings and no open critical or major defects. Inspect the job status and download its report when qualifying a hosted run.

## Pass/fail criteria

Use exact text comparisons for identity, settings, overload, diagnostics and deterministic resolution. Use the seeded statistical tolerance only for noisy readings. A hang, stale reply, unexpected queue entry or unhandled worker exception fails its case. A subset run cannot establish exit coverage. Record the command sequence, platform, observed response and pytest node for every defect.

## Severity and priority

| Severity | Impact | Priority | Scheduling rule |
| --- | --- | --- | --- |
| Critical | Crash, hang or loss of service across sessions | P0 | Block qualification and fix immediately |
| Major | Incorrect measurement, overload, configuration or diagnostic behavior | P1 | Fix and retest before release |
| Minor | Recoverable behavior with limited impact | P2 | Schedule in the next maintenance cycle |
| Cosmetic | Presentation issue with correct protocol results | P3 | Schedule with documentation or usability work |

Assign severity from user impact and priority from urgency. A resolution requires replaying the reproduction and its automated regression check. Record known limitations separately from observed failures.
