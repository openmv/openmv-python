# OpenMV Python

Python library and CLI for communicating with OpenMV cameras using Protocol V2.

## Installation

```bash
pip install openmv
```

For video streaming support (requires pygame):

```bash
pip install openmv[gui]
```

## CLI Usage

### Stream Video

```bash
# Stream from default port (/dev/ttyACM0)
openmv

# Stream from specific port
openmv --port /dev/ttyACM1

# Run a custom script
openmv --script my_script.py

# Adjust display scale
openmv --scale 2
```

### Camera Info

```bash
openmv --info
```

### Reset Camera

```bash
openmv --reset
```

### Enter Bootloader

```bash
openmv --boot
```

### Benchmark Mode

```bash
openmv --bench
```

### Controls (Stream Mode)

- `C` - Capture screenshot to `capture.png`
- `ESC` - Exit

## Library Usage

```python
from openmv import OMVCamera

# Connect to camera
with OMVCamera('/dev/ttyACM0') as camera:
    # Get system info
    info = camera.system_info()
    print(f"Firmware: {info['firmware_version']}")

    # Execute a script
    camera.exec('''
import csi
csi0 = csi.CSI()
csi0.reset()
''')

    # Read frames
    camera.streaming(True)
    while True:
        if frame := camera.read_frame():
            print(f"Frame: {frame['width']}x{frame['height']}")
```

## API Reference

### OMVCamera

Main class for camera communication.

```python
OMVCamera(
    port,               # Serial port (e.g., '/dev/ttyACM0')
    baudrate=921600,    # Serial baudrate
    crc=True,           # Enable CRC validation
    seq=True,           # Enable sequence number validation
    ack=True,           # Enable packet acknowledgment
    events=True,        # Enable event notifications
    timeout=1.0,        # Protocol timeout in seconds
    max_retry=3,        # Maximum retries
    max_payload=4096,   # Maximum payload size
)
```

#### Methods

- `connect()` / `disconnect()` - Manage connection
- `exec(script)` - Execute a MicroPython script
- `stop()` - Stop the running script
- `reset()` - Reset the camera
- `boot()` - Enter bootloader mode
- `streaming(enable, raw=False, res=None)` - Enable/disable video streaming
- `read_frame()` - Read a video frame
- `read_stdout()` - Read script output
- `read_status()` - Poll channel status
- `system_info()` - Get camera system information
- `channel_read(name)` / `channel_write(name, data)` - Custom channel I/O

### Exceptions

- `OMVPException` - Base protocol exception
- `OMVPTimeoutException` - Timeout during communication
- `OMVPChecksumException` - CRC validation failure
- `OMVPSequenceException` - Sequence number mismatch

## Requirements

- Python 3.8+
- pyserial
- numpy
- pygame (optional, for video streaming)

## License

MIT License - Copyright (c) 2025 OpenMV, LLC.
