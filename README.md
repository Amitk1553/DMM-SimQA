# DMM-SimQA

Start with the [project handbook and interview guide](docs/Project_Handbook.html) for a worked measurement, source walkthrough, case-by-case test catalog and interview practice. Download or open the HTML file locally to read or print it offline.

## Overview

DMM-SimQA simulates a single bench digital multimeter for testing SCPI control software. Run it in process for repeatable measurement tests or connect several clients to the same instrument over loopback TCP. The simulator uses the Python standard library. The QA suite adds pytest, HTML reporting and statement coverage.

## Architecture

```text
SCPIClient ---- ASCII lines / TCP ----> SCPIServer
                                            |
                                     connection workers
                                            |
pytest in-process fixtures ------------> SCPIParser
                                      one command lock
                                            |
                                        VirtualDMM
                                      /     |      \
                                settings   FIFO   signal + noise
```

Each command executes atomically. Clients share configuration, signal and the error queue. A sequence of commands can interleave with another client's sequence. Use one client per thread.

## Supported SCPI command reference

One ASCII command per line. Accepts LF or CRLF, mixed case, outer whitespace and an optional leading colon. Choose either the short or full spelling for each keyword. Separate arguments from the header with whitespace. The transport accepts up to 4096 bytes per line including LF. Oversized or incomplete frames close the connection. Invalid ASCII in a complete frame queues a syntax error.

| Command | Purpose and response |
| --- | --- |
| `*IDN?` | Returns `SimQA-Labs,DMM-34401A,SQ001234,1.2.0`. |
| `*RST` | Selects DC voltage at 100 V, sets signal to zero, turns output off and noise on, and clears errors. |
| `*CLS` | Clears the FIFO while preserving instrument settings. |
| `CONF:VOLT:DC [range]` | Sets DC voltage full scale in volts. |
| `CONF:CURR:DC [range]` | Sets DC current full scale in amperes. |
| `CONF:RES [range]` | Sets resistance full scale in ohms. |
| `CONF?` | Returns mode and range, e.g. `VOLT:DC,100.0`. |
| `OUTP ON` / `OUTP OFF` / `OUTP?` | Controls the measurement gate. Query returns `1` or `0`. |
| `SOUR:SIM <value>` | Sets the finite input in the current function's units. Accepts signed decimal and scientific notation. |
| `SOUR:NOISE ON` / `SOUR:NOISE OFF` | Enables Gaussian noise or selects deterministic readings. |
| `MEAS:VOLT:DC?` / `MEAS:CURR:DC?` / `MEAS:RES?` | Reads the indicated function. |
| `SYST:ERR?` | Removes the oldest error. An empty queue returns `0,"No error"`. |

Full keywords are CONFIGURE, VOLTAGE, CURRENT, RESISTANCE, OUTPUT, SOURCE, SIMULATE, MEASURE, SYSTEM and ERROR. DC and NOISE have one spelling. Writes have no reply. Invalid queries return their error string immediately and also queue it. Unknown headers queue -100, malformed parameters queue -102, and invalid numeric limits queue -222.

| Function | Input interval | Display resolution | Noise standard deviation |
| --- | --- | --- | --- |
| DC voltage | 0 to 100 V | 0.001 V | 0.005 V |
| DC current | 0 to 10 A | 0.001 A | 0.002 A |
| Resistance | 0 to 1,000,000 Ω | 0.1 Ω | 0.5 Ω |

A range argument must be positive and at most the function maximum. Omitting it selects that maximum. **With output off, every measurement returns formatted zero and leaves the error queue unchanged.** With output on, a mode mismatch returns and queues `-221,"Settings conflict"`. A matching query checks the true input against the inclusive interval from zero to configured full scale. An overload returns `9.9E+37` and queues `-222,"Data out of range"`. For valid inputs the meter adds optional noise, clips to the interval, then rounds for display.

## Start the simulator

Use two terminals in the repository root (the directory containing `pytest.ini`). Python 3.10 or later is required. The virtual environment keeps the QA tools local to this project. The following commands use its interpreter directly.

**Terminal 1 · Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python -m dmm_simqa.server --port 5025
```

**Terminal 1 · macOS or Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export PYTHONPATH=src
.venv/bin/python -m dmm_simqa.server --port 5025
```

Create the environment and install dependencies once. On subsequent starts, set the source path and run the last command. Wait for `Listening on 127.0.0.1:5025`. Leave this terminal running. If the port is busy, use `--port 0` and substitute the printed port for 5025 below. Stop the server with Ctrl+C after the demo.

**Terminal 2 · connect to it**

In PowerShell run the first block. On macOS or Linux run the second. Both start a Python prompt in the same project.

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python
```

```sh
PYTHONPATH=src .venv/bin/python
```

Paste this example at the Python prompt and press Enter on a blank line to finish the block. Compare the replies with the comments. The same input number means volts, amperes or ohms according to the selected function.

```python
from dmm_simqa.client import SCPIClient

with SCPIClient("127.0.0.1", 5025, timeout=2) as meter:
    meter.write("*RST")
    print(meter.query("*IDN?"))   # SimQA-Labs,DMM-34401A,SQ001234,1.2.0
    print(meter.query("CONF?"))   # VOLT:DC,100.0
    print(meter.query("OUTP?"))   # 0
    meter.write("SOUR:NOISE OFF")
    meter.write("SOUR:SIM 2.3456")
    print(meter.query("MEAS:VOLT:DC?"))  # 0.000 while output is off
    meter.write("OUTP ON")
    for mode in ("VOLT:DC", "CURR:DC", "RES"):
        meter.write(f"CONF:{mode} 5")
        print(mode, meter.query(f"MEAS:{mode}?"))
    # VOLT:DC 2.346, CURR:DC 2.346, RES 2.3
    meter.write("SOUR:SIM 5.0001")
    print(meter.query("MEAS:RES?"))  # 9.9E+37
    print(meter.query("SYST:ERR?"))  # -222,"Data out of range"
    print(meter.query("SYST:ERR?"))  # 0,"No error"
    meter.write("CONF:RES ABC")
    print(meter.query("SYST:ERR?"))  # -102,"Syntax error"
    meter.write("BAD")
    meter.write("*CLS")
    print(meter.query("SYST:ERR?"))  # 0,"No error"
    meter.write("*RST")
```

Type `exit()` to return to the shell. Opening a client connects to the existing instrument. Use `*RST` when you want fresh state.

## Test the project

The tests start their own loopback server. You can run them with the demo server stopped. From the repository root, activate the environment with `.\.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on macOS/Linux. If activation is unavailable, replace `python` in the commands below with the virtual environment's interpreter path from Terminal 1. Pytest configures the source path automatically.

| What you want to verify | Command | Expected cases |
| --- | --- | ---: |
| Identity, reset, empty queue and output switching | `python -m pytest -m smoke --no-cov -v` | 4 |
| Three modes, rounding, noise statistics, aliases and FIFO | `python -m pytest -m functional --no-cov -v` | 12 |
| Repeat the designated regression set (same functional cases) | `python -m pytest -m regression --no-cov -v` | 12 |
| Minima, full scale, negative inputs and overload before rounding | `python -m pytest -m boundary --no-cov -v` | 13 |
| Malformed commands, range rejection, disabled output and mode conflict | `python -m pytest -m negative --no-cov -v` | 15 |
| Real sockets, simultaneous clients, timeout, disconnect, framing and shutdown | `python -m pytest -m integration --no-cov -v` | 7 |
| Full suite, HTML report and coverage gate | `python -m pytest` | 51 |

To test **one exact behavior**, find its row in [Test_Cases.csv](docs/Test_Cases.csv). Read the preconditions, steps and expected result, then run the value in `Automated_Test_Function` as a quoted pytest selector. For example, this checks the 0.1 V range with an input of 0.10001 V. The meter must detect overload even though both numbers would display as 0.100 V.

```sh
python -m pytest --no-cov -v 'tests/test_boundary.py::test_overload[VOLT:DC-0.1-0.10001]'
```

Use `python -m pytest --collect-only -q --no-cov` to list the available cases. Use `python -m pytest --no-cov -vv -x` to stop at the first failure and inspect the exact inputs. Run `python -m pytest` last to regenerate the full [HTML report](reports/test_report.html). Focused runs overwrite this file and skip the repository-wide coverage threshold. The full run requires all tests to pass, treats warnings as errors and enforces 90% aggregate statement coverage.

| Symptom | Check |
| --- | --- |
| Python cannot import `dmm_simqa` | Start in the repository root and set `PYTHONPATH` in the terminal launching the server or client. |
| Pytest rejects `--html` or `--cov` | Install requirements with the same interpreter you use for `-m pytest`. |
| Connection refused | Check Terminal 1 for the listener address and copy its actual port. |
| Query times out | Use `write` for setters and `query` for headers ending in `?`. Reopen the client after a timeout. |
| Unexpected zero or overload | Query `OUTP?`, `CONF?` and `SYST:ERR?`. Check the sign and magnitude of the last simulated input. |

## QA artifacts

The [master test plan](docs/Test_Plan.md) defines acceptance criteria. The [traceability matrix](docs/Test_Cases.csv) maps each case to its exact pytest node. The [defect reports](docs/Bug_Reports.md) record reproduction conditions and regression checks. Each run writes a self-contained [HTML report](reports/test_report.html). The full run also prints missing statement lines.

## CI/CD

GitHub Actions runs the full suite on pushes and pull requests targeting main. Bitbucket Pipelines runs it on main and on pull requests. Both use Python 3.11, install the pinned QA tools and retain the HTML report as `dmm-simqa-test-report`. Test failures, warnings treated as errors and coverage below 90% fail the verification job.
