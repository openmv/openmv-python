# OpenMV Python

Python library and CLI for communicating with OpenMV cameras using Protocol V2.

## Installation

```bash
pip install openmv
```

## CLI Usage

### Stream Video

```bash
# Stream from specific port
openmv --port /dev/ttyACM0

# Run a custom script
openmv --script my_script.py

# Adjust display scale
openmv --scale 2

# Enable firmware symbols
openmv --firmware path/to/firmware.elf
```

### Benchmark Mode

```bash
openmv --bench
```

### Controls (Stream Mode)

- `ESC` - Exit
- `P` - Cycle profiler overlay (Off → Performance → Events)
- `M` - Toggle profiler mode (Inclusive ↔ Exclusive)
- `R` - Reset profiler counters

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

### Camera

Main class for camera communication.

```python
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

#### Methods

**Connection Management:**
- `connect()` / `disconnect()` - Manage connection
- `is_connected()` - Check connection status

**Script Execution:**
- `exec(script)` - Execute a MicroPython script
- `stop()` - Stop the running script

**Video Streaming:**
- `streaming(enable, raw=False, res=None)` - Enable/disable video streaming
- `read_frame()` - Read a video frame (returns dict with width, height, format, depth, data, raw_size)

**Output and Status:**
- `read_stdout()` - Read script output text
- `read_status()` - Poll channel status (returns dict of channel readiness)

**Channel Operations:**
- `has_channel(name)` - Check if a channel exists
- `channel_read(name, size=None)` - Read data from a custom channel
- `channel_write(name, data)` - Write data to a custom channel
- `channel_size(name)` - Get size of available data in a channel

**Profiler (if available):**
- `read_profile()` - Read profiler data
- `profiler_mode(exclusive)` - Set profiler mode (inclusive/exclusive)
- `profiler_reset(config=None)` - Reset profiler counters
- `profiler_event(counter_num, event_id)` - Configure event counter

**System Information:**
- `system_info()` - Get camera system information
- `host_stats()` / `device_stats()` - Get protocol statistics

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
