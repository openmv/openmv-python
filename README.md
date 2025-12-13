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

Full API documentation: [docs/api.md](https://github.com/openmv/openmv-python/blob/master/docs/api.md)

### Camera

```python
from openmv import Camera

Camera(
    port,               # Serial port (e.g., '/dev/ttyACM0')
    baudrate=921600,    # Serial baudrate
    crc=True,           # Enable CRC validation
    seq=True,           # Enable sequence number validation
    ack=True,           # Enable packet acknowledgment
    events=True,        # Enable event notifications
    timeout=1.0,        # Protocol timeout in seconds
    max_retry=3,        # Maximum retries
    max_payload=4096,   # Maximum payload size
    drop_rate=0.0,      # Packet drop simulation (testing only)
)
```

### Methods

| Method | Description |
|--------|-------------|
| `connect()` / `disconnect()` | Manage connection |
| `is_connected()` | Check connection status |
| `exec(script)` | Execute a MicroPython script |
| `stop()` | Stop the running script |
| `streaming(enable, raw=False, res=None)` | Enable/disable video streaming |
| `read_frame()` | Read video frame → `{width, height, format, depth, data, raw_size}` |
| `read_stdout()` | Read script output text |
| `read_status()` | Poll channel status → `{channel_name: bool, ...}` |
| `has_channel(name)` | Check if channel exists |
| `channel_read(name, size=None)` | Read from custom channel |
| `channel_write(name, data)` | Write to custom channel |
| `channel_size(name)` | Get available data size |
| `system_info()` | Get camera system information |
| `host_stats()` / `device_stats()` | Get protocol statistics |

#### Profiler Methods (if available)

| Method | Description |
|--------|-------------|
| `read_profile()` | Read profiler data |
| `profiler_mode(exclusive)` | Set inclusive/exclusive mode |
| `profiler_reset(config=None)` | Reset profiler counters |
| `profiler_event(counter_num, event_id)` | Configure event counter |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `OMVException` | Base protocol exception |
| `TimeoutException` | Timeout during communication |
| `ChecksumException` | CRC validation failure |
| `SequenceException` | Sequence number mismatch |

## Requirements

- Python 3.8+
- pyserial >= 3.5
- numpy >= 1.20.0
- pygame >= 2.0.0
- pyelftools

## License

MIT License - Copyright (c) 2025 OpenMV, LLC.
