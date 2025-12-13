# OpenMV Python

Python library and CLI for communicating with OpenMV cameras using Protocol V2.

## Installation

```bash
pip install openmv
```

## CLI Usage

### Examples

```bash
# Basic usage - stream video from camera
openmv --port /dev/ttyACM0

# Run a custom script
openmv --port /dev/ttyACM0 --script my_script.py

# Adjust display scale (default is 4x)
openmv --port /dev/ttyACM0 --scale 2

# Run throughput benchmark
openmv --port /dev/ttyACM0 --bench

# Load firmware symbols for profiler function names
openmv --port /dev/ttyACM0 --firmware build/firmware.elf

# Quiet mode (suppress script output)
openmv --port /dev/ttyACM0 --quiet

# Debug mode (verbose logging)
openmv --port /dev/ttyACM0 --debug
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--port PORT` | `/dev/ttyACM0` | Serial port |
| `--script FILE` | None | MicroPython script file to execute |
| `--scale N` | 4 | Display scaling factor |
| `--poll MS` | 4 | Poll rate in milliseconds |
| `--bench` | False | Run throughput benchmark mode |
| `--timeout SEC` | 1.0 | Protocol timeout in seconds |
| `--baudrate N` | 921600 | Serial baudrate |
| `--firmware FILE` | None | Firmware ELF file for profiler symbol resolution |
| `--quiet` | False | Suppress script output text |
| `--debug` | False | Enable debug logging |

#### Protocol Options

| Option | Default | Description |
|--------|---------|-------------|
| `--crc BOOL` | true | Enable CRC validation |
| `--seq BOOL` | true | Enable sequence number validation |
| `--ack BOOL` | true | Enable packet acknowledgment |
| `--events BOOL` | true | Enable event notifications |
| `--max-retry N` | 3 | Maximum number of retries |
| `--max-payload N` | 4096 | Maximum payload size in bytes |
| `--drop-rate N` | 0.0 | Packet drop simulation rate (0.0-1.0, for testing) |

### Keyboard Controls

| Key | Action |
|-----|--------|
| `ESC` | Exit |
| `P` | Cycle profiler overlay (Off → Performance → Events) |
| `M` | Toggle profiler mode (Inclusive ↔ Exclusive) |
| `R` | Reset profiler counters |

## Library Usage

```python
from openmv import Camera

script = """
import csi, time

csi0 = csi.CSI()
csi0.reset()
csi0.pixformat(csi.RGB565)
csi0.framesize(csi.QVGA)
clock = time.clock()
while True:
    clock.tick()
    img = csi0.snapshot()
    print(clock.fps(), "FPS")
"""

# Connect to camera
with Camera('/dev/ttyACM0') as camera:
    # Stop running script (if any)
    camera.stop()

    # Execute script and enable streaming
    camera.exec(script)
    camera.streaming(True, raw=False, res=(512, 512))

    # Read frames and output
    while True:
        if frame := camera.read_frame():
            print(f"Frame: {frame['width']}x{frame['height']}")

        if text := camera.read_stdout():
            print(text, end='')
```

## API Reference

See [docs/api.md](docs/api.md) for full API documentation.

### Quick Reference

```python
from openmv import Camera, OMVException, TimeoutException

with Camera('/dev/ttyACM0') as camera:
    camera.stop()                          # Stop running script
    camera.exec(script)                    # Execute script
    camera.streaming(True)                 # Enable streaming
    frame = camera.read_frame()            # Read video frame
    text = camera.read_stdout()            # Read script output
    status = camera.read_status()          # Poll channel status
    info = camera.system_info()            # Get system info
```

### Exceptions

- `OMVException` - Base protocol exception
- `TimeoutException` - Timeout during communication
- `ChecksumException` - CRC validation failure
- `SequenceException` - Sequence number mismatch

## Requirements

- Python 3.8+
- pyserial >= 3.5
- numpy >= 1.20.0
- pygame >= 2.0.0
- pyelftools

## License

MIT License - Copyright (c) 2025 OpenMV, LLC.
