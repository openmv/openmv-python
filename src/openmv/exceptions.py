# SPDX-License-Identifier: MIT
#
# Copyright (c) 2025 OpenMV, LLC.
#
# OpenMV Protocol Exceptions
#
# This module defines all the custom exceptions used in the OpenMV
# Protocol implementation for proper error handling and debugging.

import traceback


class OMVException(Exception):
    """Base exception for OpenMV protocol errors"""
    def __init__(self, message):
        super().__init__(message)
        self.traceback = traceback.format_exc()


class TimeoutException(OMVException):
    """Raised when a protocol operation times out"""
    def __init__(self, message):
        super().__init__(message)


class ChecksumException(OMVException):
    """Raised when CRC validation fails"""
    def __init__(self, message):
        super().__init__(message)


class SequenceException(OMVException):
    """Raised when sequence number validation fails"""
    def __init__(self, message):
        super().__init__(message)


class ResyncException(OMVException):
    """Raised to indicate that a resync was performed and operation should be retried"""
    def __init__(self, message="Resync performed, retry operation"):
        super().__init__(message)
