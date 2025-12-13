#!/usr/bin/env python
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2025 OpenMV, LLC.

# OpenMV CLI Tool
# Command-line interface for OpenMV cameras. Provides live video
# streaming, script execution, and camera management capabilities.

import sys
import os
import argparse
import time
import logging
import pygame
import signal
import atexit

from openmv.camera import Camera
from openmv.profiler import draw_profile_overlay


# Benchmark script for throughput testing
bench_script = """
import csi, image, time

csi0 = csi.CSI()
csi0.reset()
csi0.pixformat(csi.RGB565)
csi0.framesize(csi.QVGA)
img = csi0.snapshot().compress()
while(True):
    img.flush()
"""

# Default test script for csi-based cameras
test_script = """
import csi, image, time

csi0 = csi.CSI()
csi0.reset()
csi0.pixformat(csi.RGB565)
csi0.framesize(csi.QVGA)
clock = time.clock()

while(True):
    clock.tick()
    img = csi0.snapshot()
    print(clock.fps(), " FPS")
"""


def cleanup_and_exit():
    """Force cleanup pygame and exit"""
    try:
        pygame.quit()
    except Exception:
        pass
    os._exit(0)


def signal_handler(signum, frame):
    cleanup_and_exit()


def str2bool(v):
    """Convert string to boolean for argparse"""
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main():
    parser = argparse.ArgumentParser(description='OpenMV CLI Tool')

    parser.add_argument('--port',
                        action='store', default='/dev/ttyACM0',
                        help='Serial port (default: /dev/ttyACM0)')

    parser.add_argument("--script",
                        action="store", default=None,
                        help="Script file")

    parser.add_argument('--poll', action='store',
                        default=4, type=int,
                        help='Poll rate in ms (default: 4)')

    parser.add_argument('--scale', action='store',
                        default=4, type=int,
                        help='Display scaling factor (default: 4)')

    parser.add_argument('--bench',
                        action='store_true', default=False,
                        help='Run throughput benchmark')
    parser.add_argument('--timeout',
                        action='store', type=float, default=1.0,
                        help='Protocol timeout in seconds')

    parser.add_argument('--debug',
                        action='store_true',
                        help='Enable debug logging')

    parser.add_argument('--baudrate',
                        type=int, default=921600,
                        help='Serial baudrate (default: 921600)')

    parser.add_argument('--crc',
                        type=str2bool, nargs='?', const=True, default=True,
                        help='Enable CRC validation (default: true)')

    parser.add_argument('--seq',
                        type=str2bool, nargs='?', const=True, default=True,
                        help='Enable sequence number validation (default: true)')

    parser.add_argument('--ack',
                        type=str2bool, nargs='?', const=True, default=True,
                        help='Enable packet acknowledgment (default: false)')

    parser.add_argument('--events',
                        type=str2bool, nargs='?', const=True, default=True,
                        help='Enable event notifications (default: true)')

    parser.add_argument('--max-retry',
                        type=int, default=3,
                        help='Maximum number of retries (default: 3)')

    parser.add_argument('--max-payload',
                        type=int, default=4096,
                        help='Maximum payload size in bytes (default: 4096)')

    parser.add_argument('--drop-rate',
                        type=float, default=0.0,
                        help='Packet drop simulation rate (0.0-1.0, default: 0.0)')

    parser.add_argument('--firmware',
                        action='store', default=None,
                        help='Firmware ELF file for symbol resolution')

    parser.add_argument('--quiet',
                        action='store_true',
                        help='Suppress script output text')

    args = parser.parse_args()

    # Register signal handlers for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_and_exit)

    # Configure logging
    if args.debug:
        log_level = logging.DEBUG
    elif not args.quiet:
        log_level = logging.INFO
    else:
        log_level = logging.ERROR

    logging.basicConfig(
        format="%(relativeCreated)010.3f - %(message)s",
        level=log_level,
    )

    # Load script
    if args.script is not None:
        with open(args.script, 'r') as f:
            script = f.read()
        logging.info(f"Loaded script from {args.script}")
    else:
        script = bench_script if args.bench else test_script
        logging.info("Using built-in script")

    # Load profiler symbols if firmware provided
    symbols = []
    if args.firmware:
        from openmv.profiler import load_symbols
        symbols = load_symbols(args.firmware)

    # Initialize pygame
    pygame.init()

    screen = None
    clock = pygame.time.Clock()
    fps_clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 30)

    if not args.bench:
        pygame.display.set_caption("OpenMV Camera")
    else:
        pygame.display.set_caption("OpenMV Camera (Benchmark)")
        screen = pygame.display.set_mode((640, 120), pygame.DOUBLEBUF, 32)

    # Profiler state
    profile_view = 0  # Off
    profile_mode = False  # False = inclusive, True = exclusive
    profile_enabled = False  # Will be set if profile channel exists
    profile_update_ms = 0
    profile_data = None

    try:
        with Camera(args.port, baudrate=args.baudrate, crc=args.crc, seq=args.seq,
                    ack=args.ack, events=args.events,
                    timeout=args.timeout, max_retry=args.max_retry,
                    max_payload=args.max_payload, drop_rate=args.drop_rate) as camera:
            logging.info(f"Connected to OpenMV camera on {args.port}")

            # Configure profiler (if enabled)
            if profile_enabled := camera.has_channel("profile"):
                logging.info("Profiler channel detected - profiling enabled")
                camera.profiler_reset(config=None)

            # Stop any running script
            camera.stop()
            time.sleep(0.500)

            # Execute script
            camera.exec(script)
            camera.streaming(True, raw=False, res=(512, 512))
            logging.info("Script executed, starting display...")

            while True:
                # Handle pygame events first to keep UI responsive
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            raise KeyboardInterrupt
                        elif profile_enabled and event.key == pygame.K_p:
                            profile_view = (profile_view + 1) % 3  # Cycle views
                            logging.info(f"Profile view: {profile_view}")
                        elif profile_enabled and event.key == pygame.K_m:
                            profile_mode = not profile_mode
                            camera.profiler_mode(exclusive=profile_mode)
                            logging.info(f"Profile mode: {'Exclusive' if profile_mode else 'Inclusive'}")
                        elif profile_enabled and event.key == pygame.K_r:
                            camera.profiler_reset()
                            logging.info("Profiler reset")

                # Read camera status
                status = camera.read_status()

                # Read text output
                if not args.quiet and not args.bench and status and status.get('stdout'):
                    if text := camera.read_stdout():
                        print(text, end='')

                # Read frame data
                if frame := camera.read_frame():
                    fps = fps_clock.get_fps()
                    w, h, data = frame['width'], frame['height'], frame['data']

                    # Create image from RGB888 data (always converted by camera module)
                    if not args.bench:
                        image = pygame.image.frombuffer(data, (w, h), 'RGB')
                        image = pygame.transform.smoothscale(image, (w * args.scale, h * args.scale))

                    # Create/resize screen if needed
                    if screen is None:
                        screen = pygame.display.set_mode((w * args.scale, h * args.scale), pygame.DOUBLEBUF, 32)

                    # Draw frame
                    if args.bench:
                        screen.fill((0, 0, 0))
                    else:
                        screen.blit(image, (0, 0))

                    # Draw FPS info with accurate data rate
                    current_mbps = (fps * frame['raw_size']) / 1024**2
                    if current_mbps < 1.0:
                        rate_text = f"{current_mbps * 1024:.2f} KB/s"
                    else:
                        rate_text = f"{current_mbps:.2f} MB/s"
                    fps_text = f"{fps:.2f} FPS {rate_text} {w}x{h} RGB888"
                    screen.blit(font.render(fps_text, True, (255, 0, 0)), (0, 0))

                    fps_clock.tick()

                # Read profiler data if enabled (max 10Hz)
                if profile_enabled and profile_view and screen is not None:
                    current_time = time.time()
                    if current_time - profile_update_ms >= 0.1:  # 10Hz
                        if profile_data := camera.read_profile():
                            profile_update_ms = current_time

                    # Draw profiler overlay if enabled and data available
                    if profile_data is not None:
                        screen_width, screen_height = screen.get_size()
                        draw_profile_overlay(screen, screen_width, screen_height,
                                             profile_data, profile_mode, profile_view, 1, symbols)

                # Update display once at the end
                if frame:
                    pygame.display.flip()

                # Control main loop timing
                clock.tick(1000 // args.poll)

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    except Exception as e:
        logging.error(f"Error: {e}")
        if args.debug:
            import traceback
            logging.error(f"{traceback.format_exc()}")
        sys.exit(1)
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
