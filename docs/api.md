# API Reference

## Camera Class

The `Camera` class provides the main interface for communicating with OpenMV cameras.

### Constructor

```python
Camera(
    port,
    baudrate=921600,
    crc=True,
    seq=True,
    ack=True,
    events=True,
    timeout=1.0,
    max_retry=3,
    max_payload=4096,
    drop_rate=0.0
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | str | required | Serial port path (e.g., `/dev/ttyACM0`, `COM3`) |
| `baudrate` | int | 921600 | Serial communication baudrate |
| `crc` | bool | True | Enable CRC validation for packet integrity |
| `seq` | bool | True | Enable sequence number validation |
| `ack` | bool | True | Enable packet acknowledgment |
| `events` | bool | True | Enable event notifications from device |
| `timeout` | float | 1.0 | Protocol timeout in seconds |
| `max_retry` | int | 3 | Maximum number of retry attempts |
| `max_payload` | int | 4096 | Maximum payload size in bytes |
| `drop_rate` | float | 0.0 | Packet drop simulation rate for testing (0.0-1.0) |

#### Context Manager

The `Camera` class supports context manager protocol:

```python
from openmv import Camera

with Camera('/dev/ttyACM0') as camera:
    # Camera is connected
    camera.exec(script)
# Camera is automatically disconnected
```

---

## Connection Methods

### connect()

Establish connection to the OpenMV camera.

```python
camera.connect()
```

Called automatically when using context manager.

**Raises:** `OMVException` if connection fails.

---

### disconnect()

Close connection to the OpenMV camera.

```python
camera.disconnect()
```

Called automatically when exiting context manager.

---

### is_connected()

Check if connected to camera.

```python
connected = camera.is_connected()
```

**Returns:** `bool` - True if connected.

---

## Script Execution

### exec(script)

Execute a MicroPython script on the camera.

```python
camera.exec(script)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `script` | str | MicroPython script source code |

#### Example

```python
script = """
import csi
csi0 = csi.CSI()
csi0.reset()
"""
camera.exec(script)
```

---

### stop()

Stop the currently running script.

```python
camera.stop()
```

---

## Video Streaming

### streaming(enable, raw=False, res=None)

Enable or disable video streaming.

```python
camera.streaming(True, raw=False, res=(512, 512))
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable` | bool | required | Enable or disable streaming |
| `raw` | bool | False | Enable raw streaming mode |
| `res` | tuple | None | Resolution tuple (width, height) for raw mode |

---

### read_frame()

Read a video frame from the stream buffer.

```python
frame = camera.read_frame()
```

**Returns:** `dict` or `None` - Frame data dictionary, or None if no frame available.

#### Return Value

| Key | Type | Description |
|-----|------|-------------|
| `width` | int | Frame width in pixels |
| `height` | int | Frame height in pixels |
| `format` | int | Pixel format code |
| `depth` | int | Bit depth |
| `data` | bytes | RGB888 pixel data |
| `raw_size` | int | Original raw data size before conversion |

#### Example

```python
while True:
    if frame := camera.read_frame():
        print(f"Frame: {frame['width']}x{frame['height']}")
        # frame['data'] contains RGB888 bytes
```

---

## Output and Status

### read_stdout()

Read script output text from the stdout buffer.

```python
text = camera.read_stdout()
```

**Returns:** `str` or `None` - Output text, or None if buffer empty.

#### Example

```python
if text := camera.read_stdout():
    print(text, end='')
```

---

### read_status()

Poll channel status to check data availability.

```python
status = camera.read_status()
```

**Returns:** `dict` - Dictionary mapping channel names to boolean readiness.

#### Example

```python
status = camera.read_status()
if status.get('stdout'):
    text = camera.read_stdout()
if status.get('stream'):
    frame = camera.read_frame()
```

---

## Channel Operations

### has_channel(name)

Check if a named channel exists.

```python
exists = camera.has_channel('profile')
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Channel name |

**Returns:** `bool` - True if channel exists.

---

### channel_read(name, size=None)

Read data from a custom channel.

```python
data = camera.channel_read('buffer')
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Channel name |
| `size` | int | None | Number of bytes to read (None = all available) |

**Returns:** `bytes` or `None` - Channel data, or None if channel not found.

---

### channel_write(name, data)

Write data to a custom channel.

```python
success = camera.channel_write('buffer', b'\x01\x02\x03')
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Channel name |
| `data` | bytes | Data to write |

**Returns:** `bool` - True if successful.

---

### channel_size(name)

Get size of data available in a channel.

```python
size = camera.channel_size('buffer')
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Channel name |

**Returns:** `int` - Number of bytes available.

---

## Profiler

Profiler methods are only available when the camera firmware is built with profiling enabled and a `profile` channel is registered.

### read_profile()

Read profiler data from the profile channel.

```python
records = camera.read_profile()
```

**Returns:** `list` or `None` - List of profile record dictionaries, or None if unavailable.

#### Profile Record Fields

| Key | Type | Description |
|-----|------|-------------|
| `address` | int | Function address |
| `caller` | int | Caller address |
| `call_count` | int | Number of calls |
| `min_ticks` | int | Minimum execution ticks |
| `max_ticks` | int | Maximum execution ticks |
| `total_ticks` | int | Total execution ticks |
| `total_cycles` | int | Total CPU cycles |
| `events` | tuple | Event counter values |

---

### profiler_mode(exclusive)

Set profiler mode.

```python
camera.profiler_mode(exclusive=True)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `exclusive` | bool | True for exclusive mode, False for inclusive |

**Inclusive mode:** Counts include time spent in called functions.
**Exclusive mode:** Counts exclude time spent in called functions.

---

### profiler_reset(config=None)

Reset profiler counters and optionally configure event counters.

```python
camera.profiler_reset()
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | list | None | Event configuration (None uses defaults) |

When `config=None`, configures default events: CPU cycles, L1I cache, L1D cache, L2D cache.

---

### profiler_event(counter_num, event_id)

Configure a specific event counter.

```python
camera.profiler_event(0, 0x0039)  # CPU cycles
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `counter_num` | int | Counter index (0-7) |
| `event_id` | int | ARM PMU event ID |

---

## System Information

### system_info()

Get camera system information.

```python
info = camera.system_info()
```

**Returns:** `dict` - System information dictionary.

#### Return Value

| Key | Type | Description |
|-----|------|-------------|
| `cpu_id` | int | CPU identifier |
| `device_id` | tuple | Device ID (3 words) |
| `sensor_chip_id` | tuple | Sensor chip IDs (3 words) |
| `usb_vid` | int | USB Vendor ID |
| `usb_pid` | int | USB Product ID |
| `gpu_present` | bool | GPU available |
| `npu_present` | bool | NPU available |
| `isp_present` | bool | ISP available |
| `venc_present` | bool | Video encoder available |
| `jpeg_present` | bool | JPEG encoder available |
| `dram_present` | bool | DRAM available |
| `crc_present` | bool | Hardware CRC available |
| `pmu_present` | bool | PMU available |
| `pmu_eventcnt` | int | Number of PMU event counters |
| `wifi_present` | bool | WiFi available |
| `bt_present` | bool | Bluetooth available |
| `sd_present` | bool | SD card available |
| `eth_present` | bool | Ethernet available |
| `usb_highspeed` | bool | USB High-Speed capable |
| `multicore_present` | bool | Multi-core capable |
| `flash_size_kb` | int | Flash size in KB |
| `ram_size_kb` | int | RAM size in KB |
| `framebuffer_size_kb` | int | Framebuffer size in KB |
| `stream_buffer_size_kb` | int | Stream buffer size in KB |
| `firmware_version` | bytes | Firmware version (3 bytes) |
| `protocol_version` | bytes | Protocol version (3 bytes) |
| `bootloader_version` | bytes | Bootloader version (3 bytes) |

---

### host_stats()

Get host-side protocol statistics.

```python
stats = camera.host_stats()
```

**Returns:** `dict` - Host statistics from transport layer.

---

### device_stats()

Get device-side protocol statistics.

```python
stats = camera.device_stats()
```

**Returns:** `dict` - Device statistics dictionary.

#### Return Value

| Key | Type | Description |
|-----|------|-------------|
| `sent` | int | Packets sent |
| `received` | int | Packets received |
| `checksum` | int | Checksum errors |
| `sequence` | int | Sequence errors |
| `retransmit` | int | Retransmissions |
| `transport` | int | Transport errors |
| `sent_events` | int | Events sent |
| `max_ack_queue_depth` | int | Maximum ACK queue depth |

---

## Exceptions

### OMVException

Base exception for all protocol errors.

```python
from openmv import OMVException

try:
    camera.connect()
except OMVException as e:
    print(f"Protocol error: {e}")
```

---

### TimeoutException

Raised when a protocol operation times out.

```python
from openmv import TimeoutException

try:
    frame = camera.read_frame()
except TimeoutException:
    print("Read timed out")
```

---

### ChecksumException

Raised when CRC validation fails.

```python
from openmv import ChecksumException
```

---

### SequenceException

Raised when sequence number validation fails.

```python
from openmv import SequenceException
```
