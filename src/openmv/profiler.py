# SPDX-License-Identifier: MIT
#
# Copyright (c) 2025 OpenMV, LLC.
#
# OpenMV Profiler Visualization
#
# This module provides profiler visualization functions for OpenMV cameras.
# It handles symbol loading, colorization, and rendering of profiler data.

import logging
import pygame


def load_symbols(firmware_path):
    """Load symbols from an ELF firmware file.

    Args:
        firmware_path: Path to ELF file

    Returns:
        List of tuples (start_addr, end_addr, name) sorted by address,
        or empty list if loading fails
    """
    try:
        from elftools.elf.elffile import ELFFile
    except ImportError:
        logging.error("elftools package not installed. Install with: pip install pyelftools")
        return []

    symbols = []
    try:
        with open(firmware_path, 'rb') as f:
            elf = ELFFile(f)
            symtab = elf.get_section_by_name('.symtab')
            if not symtab:
                logging.warning("No symbol table found in ELF file")
            else:
                for sym in symtab.iter_symbols():
                    addr = sym['st_value']
                    size = sym['st_size']
                    name = sym.name
                    if name and size > 0:  # ignore empty symbols
                        symbols.append((addr, addr + size, name))
                symbols.sort()
                logging.info(f"Loaded {len(symbols)} symbols from {firmware_path}")
    except Exception as e:
        logging.error(f"Failed to load symbols from {firmware_path}: {e}")

    return symbols


def addr_to_symbol(symbols, address):
    """Binary search for symbol name by address.

    Args:
        symbols: List of (start, end, name) tuples sorted by start address
        address: Address to look up

    Returns:
        Symbol name or None if not found
    """
    lo, hi = 0, len(symbols) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        start, end, name = symbols[mid]
        if start <= address < end:
            return name
        elif address < start:
            hi = mid - 1
        else:
            lo = mid + 1
    return None


def get_color_by_percentage(percentage, base_color=(220, 220, 220)):
    """Return a color based on percentage with fine-grained intensity levels.

    Args:
        percentage: Value from 0-100
        base_color: RGB tuple for 0% (default grey)

    Returns:
        RGB tuple with gradient from green (low) to red (high)
    """
    def clamp(value):
        return max(0, min(255, int(value)))

    if percentage >= 50:
        # Very high - bright red
        intensity = min(1.0, (percentage - 50) / 50)
        return (255, clamp(120 - 120 * intensity), clamp(120 - 120 * intensity))
    elif percentage >= 30:
        # High - red-orange
        intensity = (percentage - 30) / 20
        return (255, clamp(160 + 40 * intensity), clamp(160 - 40 * intensity))
    elif percentage >= 20:
        # Medium-high - orange
        intensity = (percentage - 20) / 10
        return (255, clamp(200 + 55 * intensity), clamp(180 - 20 * intensity))
    elif percentage >= 15:
        # Medium - yellow-orange
        intensity = (percentage - 15) / 5
        return (255, clamp(220 + 35 * intensity), clamp(180 + 20 * intensity))
    elif percentage >= 10:
        # Medium-low - yellow
        intensity = (percentage - 10) / 5
        return (clamp(255 - 75 * intensity), 255, clamp(180 + 75 * intensity))
    elif percentage >= 5:
        # Low - light green
        intensity = (percentage - 5) / 5
        return (clamp(180 + 75 * intensity), 255, clamp(180 + 75 * intensity))
    elif percentage >= 2:
        # Very low - green
        intensity = (percentage - 2) / 3
        return (clamp(160 + 95 * intensity), clamp(255 - 55 * intensity), clamp(160 + 95 * intensity))
    elif percentage >= 1:
        # Minimal - light blue-green
        intensity = (percentage - 1) / 1
        return (clamp(140 + 120 * intensity), clamp(200 + 55 * intensity), clamp(255 - 95 * intensity))
    else:
        # Zero or negligible - base color
        return base_color


def draw_rounded_rect(surface, color, rect, radius=5):
    """Draw a rounded rectangle on a pygame surface."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return

    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)


def draw_table(overlay_surface, config, title, headers, col_widths):
    """Draw the common table background, title, and header."""
    # Draw main table background
    table_rect = (0, 0, config['width'], config['height'])
    draw_rounded_rect(overlay_surface, config['colors']['bg'], table_rect, int(8 * config['scale_factor']))
    pygame.draw.rect(overlay_surface, config['colors']['border'], table_rect, max(1, int(2 * config['scale_factor'])))

    # Table title
    title_text = config['fonts']['title'].render(title, True, config['colors']['header_text'])
    title_rect = title_text.get_rect()
    title_x = (config['width'] - title_rect.width) // 2
    overlay_surface.blit(title_text, (title_x, int(12 * config['scale_factor'])))

    # Header
    header_y = int(50 * config['scale_factor'])
    header_height = int(40 * config['scale_factor'])

    # Draw header background
    header_rect = (int(5 * config['scale_factor']), header_y,
                   config['width'] - int(10 * config['scale_factor']), header_height)
    draw_rounded_rect(overlay_surface, config['colors']['header_bg'], header_rect, int(4 * config['scale_factor']))

    # Draw header text and separators
    current_x = int(10 * config['scale_factor'])
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        header_surface = config['fonts']['header'].render(header, True, config['colors']['header_text'])
        overlay_surface.blit(header_surface, (current_x, header_y + int(6 * config['scale_factor'])))

        if i < len(headers) - 1:
            sep_x = current_x + width - int(5 * config['scale_factor'])
            pygame.draw.line(overlay_surface, config['colors']['border'],
                             (sep_x, header_y + 2), (sep_x, header_y + header_height - 2), 1)
        current_x += width


def draw_event_table(overlay_surface, config, profile_data, profile_mode, symbols):
    """Draw the event counter mode table."""
    # Prepare data
    num_events = len(profile_data[0]['events']) if profile_data else 0
    if not num_events:
        sorted_data = sorted(profile_data, key=lambda x: x['address'])
    else:
        sort_func = lambda x: x['events'][0] // max(1, x['call_count']) # noqa
        sorted_data = sorted(profile_data, key=sort_func, reverse=True)

    headers = ["Function"] + [f"E{i}" for i in range(num_events)]
    proportions = [0.30] + [0.70 / num_events] * num_events
    col_widths = [config['width'] * prop for prop in proportions]
    profile_mode_str = "Exclusive" if profile_mode else "Inclusive"

    # Calculate event totals for percentage calculation
    event_totals = [0] * num_events
    for record in sorted_data:
        for i, event_count in enumerate(record['events']):
            event_totals[i] += event_count // max(1, record['call_count'])

    # Draw table structure
    draw_table(overlay_surface, config, f"Event Counters ({profile_mode_str})", headers, col_widths)

    # Draw data rows
    row_height = int(30 * config['scale_factor'])
    data_start_y = int(50 * config['scale_factor'] + 40 * config['scale_factor'] + 8 * config['scale_factor'])
    available_height = config['height'] - data_start_y - int(60 * config['scale_factor'])
    visible_rows = min(len(sorted_data), available_height // row_height)

    for i in range(visible_rows):
        record = sorted_data[i]
        row_y = data_start_y + i * row_height

        # Draw row background
        row_color = config['colors']['row_alt'] if i % 2 == 0 else config['colors']['row_normal']
        row_rect = (int(5 * config['scale_factor']), row_y,
                    config['width'] - int(10 * config['scale_factor']), row_height)
        pygame.draw.rect(overlay_surface, row_color, row_rect)

        # Function name
        name = addr_to_symbol(symbols, record['address']) if symbols else "<no symbols>"
        max_name_chars = int(col_widths[0] // (11 * config['scale_factor']))
        display_name = name if len(name) <= max_name_chars else name[:max_name_chars - 3] + "..."

        row_data = [display_name]

        # Event data
        for j, event_count in enumerate(record['events']):
            event_scale = ""
            event_count //= max(1, record['call_count'])
            if event_count > 1_000_000_000:
                event_count //= 1_000_000_000
                event_scale = "B"
            elif event_count > 1_000_000:
                event_count //= 1_000_000
                event_scale = "M"
            row_data.append(f"{event_count:,}{event_scale}")

        # Determine row color based on sorting key (event 0)
        if len(record['events']) > 0 and event_totals[0] > 0:
            sort_key_value = record['events'][0] // max(1, record['call_count'])
            percentage = (sort_key_value / event_totals[0] * 100)
            row_text_color = get_color_by_percentage(percentage, config['colors']['content_text'])
        else:
            row_text_color = config['colors']['content_text']

        # Draw row data with uniform color
        current_x = 10
        for j, (data, width) in enumerate(zip(row_data, col_widths)):
            text_surface = config['fonts']['content'].render(str(data), True, row_text_color)
            overlay_surface.blit(text_surface, (current_x, row_y + int(8 * config['scale_factor'])))

            if j < len(row_data) - 1:
                sep_x = current_x + width - 8
                pygame.draw.line(overlay_surface, (60, 70, 85),
                                 (sep_x, row_y), (sep_x, row_y + row_height), 1)
            current_x += width

    # Draw summary
    summary_y = config['height'] - int(50 * config['scale_factor'])
    total_functions = len(profile_data)
    grand_total = sum(event_totals)
    summary_text = (
        f"Profiles: {total_functions} | "
        f"Events: {num_events} | "
        f"Total Events: {grand_total:,}"
    )

    summary_surface = config['fonts']['summary'].render(summary_text, True, config['colors']['content_text'])
    summary_rect = summary_surface.get_rect()
    summary_x = (config['width'] - summary_rect.width) // 2
    overlay_surface.blit(summary_surface, (summary_x, summary_y))

    # Instructions
    instruction_str = "Press 'P' to toggle profiler overlay"
    instruction_text = config['fonts']['instruction'].render(instruction_str, True, (180, 180, 180))
    overlay_surface.blit(instruction_text, (0, summary_y + int(20 * config['scale_factor'])))


def draw_profile_table(overlay_surface, config, profile_data, profile_mode, symbols):
    """Draw the profile mode table."""
    # Prepare data
    sort_func = lambda x: x['total_ticks'] # noqa
    sorted_data = sorted(profile_data, key=sort_func, reverse=True)
    total_ticks_all = sum(record['total_ticks'] for record in profile_data)
    profile_mode_str = "Exclusive" if profile_mode else "Inclusive"

    headers = ["Function", "Calls", "Min", "Max", "Total", "Avg", "Cycles", "%"]
    proportions = [0.30, 0.08, 0.10, 0.10, 0.13, 0.10, 0.13, 0.05]
    col_widths = [config['width'] * prop for prop in proportions]

    # Draw table structure
    draw_table(overlay_surface, config, f"Performance Profile ({profile_mode_str})", headers, col_widths)

    # Draw data rows
    row_height = int(30 * config['scale_factor'])
    data_start_y = int(50 * config['scale_factor'] + 40 * config['scale_factor'] + 8 * config['scale_factor'])
    available_height = config['height'] - data_start_y - int(60 * config['scale_factor'])
    visible_rows = min(len(sorted_data), available_height // row_height)

    for i in range(visible_rows):
        record = sorted_data[i]
        row_y = data_start_y + i * row_height

        # Draw row background
        row_color = config['colors']['row_alt'] if i % 2 == 0 else config['colors']['row_normal']
        row_rect = (int(5 * config['scale_factor']), row_y,
                    config['width'] - int(10 * config['scale_factor']), row_height)
        pygame.draw.rect(overlay_surface, row_color, row_rect)

        # Function name
        name = addr_to_symbol(symbols, record['address']) if symbols else "<no symbols>"
        max_name_chars = int(col_widths[0] // (11 * config['scale_factor']))
        display_name = name if len(name) <= max_name_chars else name[:max_name_chars - 3] + "..."

        # Calculate values
        call_count = record['call_count']
        min_ticks = record['min_ticks'] if call_count else 0
        max_ticks = record['max_ticks'] if call_count else 0
        total_ticks = record['total_ticks']
        avg_cycles = record['total_cycles'] // max(1, call_count)
        avg_ticks = total_ticks // max(1, call_count)
        percentage = (total_ticks / total_ticks_all * 100) if total_ticks_all else 0

        ticks_scale = ""
        if total_ticks > 1_000_000_000:
            total_ticks //= 1_000_000
            ticks_scale = "M"

        row_data = [
            display_name,
            f"{call_count:,}",
            f"{min_ticks:,}",
            f"{max_ticks:,}",
            f"{total_ticks:,}{ticks_scale}",
            f"{avg_ticks:,}",
            f"{avg_cycles:,}",
            f"{percentage:.1f}%"
        ]

        # Determine row color based on percentage
        text_color = get_color_by_percentage(percentage, config['colors']['content_text'])

        # Draw row data
        current_x = int(10 * config['scale_factor'])
        for j, (data, width) in enumerate(zip(row_data, col_widths)):
            text_surface = config['fonts']['content'].render(str(data), True, text_color)
            overlay_surface.blit(text_surface, (current_x, row_y + int(8 * config['scale_factor'])))

            if j < len(row_data) - 1:
                sep_x = current_x + width - int(8 * config['scale_factor'])
                pygame.draw.line(overlay_surface, (60, 70, 85),
                                 (sep_x, row_y), (sep_x, row_y + row_height), 1)
            current_x += width

    # Draw summary
    summary_y = config['height'] - int(50 * config['scale_factor'])
    total_calls = sum(record['call_count'] for record in profile_data)
    total_cycles = sum(record['total_cycles'] for record in profile_data)
    total_ticks_summary = sum(record['total_ticks'] for record in profile_data)

    summary_text = (
        f"Profiles: {len(profile_data)} | "
        f"Total Calls: {total_calls:,} | "
        f"Total Ticks: {total_ticks_summary:,} | "
        f"Total Cycles: {total_cycles:,}"
    )

    summary_surface = config['fonts']['summary'].render(summary_text, True, config['colors']['content_text'])
    summary_rect = summary_surface.get_rect()
    summary_x = (config['width'] - summary_rect.width) // 2
    overlay_surface.blit(summary_surface, (summary_x, summary_y))

    # Instructions
    instruction_str = "Press 'P' to toggle profiler overlay"
    instruction_text = config['fonts']['instruction'].render(instruction_str, True, (180, 180, 180))
    overlay_surface.blit(instruction_text, (0, summary_y + int(20 * config['scale_factor'])))


def draw_profile_overlay(screen, screen_width, screen_height, profile_data,
                         profile_mode, profile_view, scale, symbols, alpha=250):
    """Main entry point for drawing the profile overlay.

    Args:
        screen: pygame surface to draw on
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        profile_data: List of profile records from camera
        profile_mode: Boolean, True=exclusive, False=inclusive
        profile_view: 1=performance, 2=events
        scale: Display scale factor
        symbols: List of (start, end, name) symbol tuples or empty list
        alpha: Transparency (0-255)
    """
    # Calculate dimensions and create surface
    base_width, base_height = 800, 800
    screen_width *= scale
    screen_height *= scale
    scale_factor = min(screen_width / base_width, screen_height / base_height)

    overlay_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay_surface.set_alpha(alpha)

    # Setup common configuration
    config = {
        'width': screen_width,
        'height': screen_height,
        'scale_factor': scale_factor,
        'colors': {
            'bg': (40, 50, 65),
            'border': (70, 80, 100),
            'header_bg': (60, 80, 120),
            'header_text': (255, 255, 255),
            'content_text': (220, 220, 220),
            'row_alt': (35, 45, 60),
            'row_normal': (45, 55, 70)
        },
        'fonts': {
            'title': pygame.font.SysFont("arial", int(28 * scale_factor), bold=True),
            'header': pygame.font.SysFont("monospace", int(20 * scale_factor), bold=True),
            'content': pygame.font.SysFont("monospace", int(18 * scale_factor)),
            'summary': pygame.font.SysFont("arial", int(20 * scale_factor)),
            'instruction': pygame.font.SysFont("arial", int(22 * scale_factor))
        }
    }

    # Draw based on mode
    if profile_view == 1:
        draw_profile_table(overlay_surface, config, profile_data, profile_mode, symbols)
    elif profile_view == 2:
        draw_event_table(overlay_surface, config, profile_data, profile_mode, symbols)

    screen.blit(overlay_surface, (0, 0))
