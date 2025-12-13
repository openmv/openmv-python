# SPDX-License-Identifier: MIT
#
# Copyright (c) 2025 OpenMV, LLC.
#
# OpenMV Protocol Package
#
# This package provides a Python implementation of the OpenMV Protocol
# for communicating with OpenMV cameras.
#
# Main classes:
#     Camera: High-level camera interface with channel operations
#
# Main exceptions:
#     OMVException: Base exception for protocol errors
#     TimeoutException: Timeout during protocol operations
#     ChecksumException: CRC validation failures
#     SequenceException: Sequence number validation failures

from .camera import Camera
from .exceptions import (
    OMVException,
    TimeoutException,
    ChecksumException,
    SequenceException
)

__version__ = "2.0.0"

__all__ = [
    'Camera',
    'OMVException',
    'TimeoutException',
    'ChecksumException',
    'SequenceException'
]
