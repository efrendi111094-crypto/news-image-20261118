#!/usr/bin/env python3
"""Sum up 18 November 2026's world news in one image.

Entrypoint for the make.fun news-image-20261118 bounty. Pure standard
library: draws a 1024x1024 newspaper-style poster with a hand-built 5x7
bitmap font, encodes the PNG bytes itself (zlib + struct), and writes
exactly one file: /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

The news content lives in news.json next to this file, so the stories can
be refreshed near the deadline without touching the generator. Rendering
is fully deterministic: same news.json always yields the same PNG bytes.
"""

import json
import math
import os
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

# --- Palette (newsprint) -------------------------------------------------
PAPER = (246, 241, 227)
INK = (25, 25, 25)
RED = (179, 38, 30)
WHITE = (255, 255, 255)
NAVY = (31, 58, 95)
NAVY_DARK = (22, 35, 58)
SEA = (31, 78, 121)
SEA_DARK = (22, 50, 79)
SAND = (217, 197, 138)
SKY = (220, 233, 245)
GOLD = (201, 162, 39)
TEAL = (31, 111, 107)
GRAY = (107, 107, 107)
LIGHT_PINK = (246, 227, 224)
LIGHT_PANEL = (239, 231, 211)
ORANGE = (230, 126, 34)

# --- 5x7 bitmap font ------------------------------------------------------
# Each glyph is 7 rows of 5 pixels, '1' = ink. Uppercase, digits and
# punctuation only; all rendered text is uppercased first.
FONT = {
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'C': ('01110', '10001', '10000', '10000', '10000', '10001', '01110'),
    'D': ('11100', '10010', '10001', '10001', '10001', '10010', '11100'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01111'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('01110', '00100', '00100', '00100', '00100', '00100', '01110'),
    'J': ('00111', '00010', '00010', '00010', '00010', '10010', '01100'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10101', '10001', '10001', '10001'),
    'N': ('10001', '11001', '10101', '10011', '10001', '10001', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
    'Q': ('01110', '10001', '10001', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10001', '10101', '10101', '10101', '01010'),
    'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
    'Y': ('10001', '10001', '01010', '00100', '00100', '00100', '00100'),
    'Z': ('11111', '00001', '00010', '00100', '01000', '10000', '11111'),
    '0': ('01110', '10001', '10011', '10101', '11001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11111', '00010', '00100', '00010', '00001', '10001', '01110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '11110', '00001', '00001', '10001', '01110'),
    '6': ('00110', '01000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00010', '01100'),
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
    '.': ('00000', '00000', '00000', '00000', '00000', '01100', '01100'),
    ',': ('00000', '00000', '00000', '00000', '01100', '00100', '01000'),
    ':': ('00000', '01100', '01100', '00000', '01100', '01100', '00000'),
    ';': ('00000', '01100', '01100', '00000', '01100', '00100', '01000'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    '?': ('01110', '10001', '00001', '00110', '00100', '00000', '00100'),
    '-': ('00000', '00000', '00000', '01110', '00000', '00000', '00000'),
    "'": ('00100', '00100', '01000', '00000', '00000', '00000', '00000'),
    '(': ('00010', '00100', '01000', '01000', '01000', '00100', '00010'),
    ')': ('01000', '00100', '00010', '00010', '00010', '00100', '01000'),
    '/': ('00001', '00010', '00010', '00100', '01000', '01000', '10000'),
    '&': ('01100', '10010', '10100', '01000', '10101', '10010', '01101'),
    '%': ('11001', '11010', '00010', '00100', '01000', '01011', '10011'),
    '+': ('00000', '00100', '00100', '01110', '00100', '00100', '00000'),
    '$': ('00100', '01111', '10100', '01110', '00101', '11110', '00100'),
    '#': ('01010', '01010', '11111', '01010', '11111', '01010', '01010'),
    '=': ('00000', '00000', '11111', '00000', '11111', '00000', '00000'),
    '*': ('00000', '10101', '01110', '11111', '01110', '10101', '00000'),
    '"': ('01010', '01010', '00000', '00000', '00000', '00000', '00000'),
    '_': ('00000', '00000', '00000', '00000', '00000', '00000', '11111'),
    '|': ('00100', '00100', '00100', '00100', '00100', '00100', '00100'),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (no trailing spacing)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Word-wrap text into lines that fit max_width pixels at scale."""
    words = text.split()
    lines = []
    current = ''
    for word in words:
        trial = word if not current else current + ' ' + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            # Hard-split a single word that is too long on its own.
            while text_width(word, scale) > max_width:
                n = max_width // (6 * scale)
                lines.append(word[:n])
                word = word[n:]
            current = word
    if current:
        lines.append(current)
    return lines or ['']


# --- Canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def border(self, x, y, w, h, color, thick=2):
        self.rect(x, y, w, thick, color)
        self.rect(x, y + h - thick, w, thick, color)
        self.rect(x, y, thick, h, color)
        self.rect(x + w - thick, y, thick, h, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with square brush of side `thick`."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = thick // 2
        while True:
            self.rect(x0 - r, y0 - r, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, radius, color):
        for yy in range(cy - radius, cy + radius + 1):
            dx = int((radius * radius - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= radius else 0
            self.rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, radius, color, thick=2):
        for yy in range(cy - radius, cy + radius + 1):
            for xx in range(cx - radius, cx + radius + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (radius - thick) ** 2 <= d2 <= radius * radius:
                    self.px(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Filled triangle via scanlines."""
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts

        def edge_x(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])

        for y in range(ay, cy + 1):
            if y < by:
                xa = edge_x(y, (ax, ay), (bx, by))
            else:
                xa = edge_x(y, (bx, by), (cx, cy))
            xb = edge_x(y, (ax, ay), (cx, cy))
            lo, hi = sorted([int(round(xa)), int(round(xb))])
            self.rect(lo, y, hi - lo + 1, 1, color)

    def starburst(self, cx, cy, radius, color, rays=10):
        for k in range(rays):
            ang = 2 * math.pi * k / rays
            c = int(radius * math.cos(ang))
            s = int(radius * math.sin(ang))
            self.line(cx, cy, cx + c, cy + s, color, thick=3)
        self.disc(cx, cy, max(3, radius // 3), color)

    def text(self, x, y, s, color, string, align='left'):
        string = string.upper()
        if align == 'center':
            x -= text_width(string, s) // 2
        elif align == 'right':
            x -= text_width(string, s)
        for ci, ch in enumerate(string):
            glyph = FONT.get(ch, FONT['?'])
            gx = x + ci * 6 * s
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '1':
                        self.rect(gx + col * s, y + row * s, s, s, color)

    def para(self, x, y, w, scale, color, string, leading=None, max_lines=None):
        """Wrapped paragraph; returns the y just below the last line."""
        if leading is None:
            leading = 7 * scale + 3
        lines = wrap_text(string.upper(), w, scale)
        if max_lines:
            lines = lines[:max_lines]
        for i, line in enumerate(lines):
            self.text(x, y + i * leading, scale, color, line)
        return y + len(lines) * leading


# --- Icons -----------------------------------------------------------------
def icon_gulf(cv, x, y, w, h):
    """Stylised Gulf scene: sea, land, strait, island, bursts, drones."""
    cv.rect(x, y, w, h, SEA)
    cv.rect(x, y, w, 26, SEA_DARK)
    # Landmasses (sand) top-left and bottom-right.
    cv.triangle(x, y + 26, x + 150, y + 26, x, y + 120, SAND)
    cv.rect(x, y + 26, 120, 40, SAND)
    cv.triangle(x + w, y + h, x + w - 170, y + h, x + w, y + h - 110, SAND)
    cv.rect(x + w - 130, y + h - 46, 130, 46, SAND)
    # Island in the strait.
    cv.disc(x + 190, y + 150, 22, SAND)
    cv.disc(x + 190, y + 150, 14, (196, 172, 110))
    # Route dashes across the strait.
    for i in range(6):
        cv.rect(x + 40 + i * 48, y + 210 - i * 8, 22, 5, WHITE)
    # Explosions.
    cv.starburst(x + 120, y + 130, 26, ORANGE)
    cv.starburst(x + 120, y + 130, 14, RED)
    cv.starburst(x + 268, y + 90, 20, ORANGE)
    cv.starburst(x + 268, y + 90, 10, RED)
    # Drones: small dark crosses.
    for dx, dy in ((90, 70), (300, 160), (230, 210)):
        cv.rect(x + dx - 10, y + dy - 2, 20, 4, INK)
        cv.rect(x + dx - 2, y + dy - 8, 4, 16, INK)
        cv.disc(x + dx, y + dy, 3, INK)


def icon_summit(cv, x, y, w, h):
    """Three flags on poles: China, Russia, USA."""
    cv.rect(x, y, w, h, SKY)
    cv.rect(x, y + h - 12, w, 4, INK)
    poles = [x + 8, x + 30, x + 52]
    # China: red flag, yellow star dot.
    cv.vline(poles[0], y + 8, h - 20, INK, 2)
    cv.rect(poles[0] + 2, y + 8, 16, 14, RED)
    cv.disc(poles[0] + 7, y + 15, 3, GOLD)
    # Russia: white / blue / red stripes.
    cv.vline(poles[1], y + 8, h - 20, INK, 2)
    cv.rect(poles[1] + 2, y + 8, 16, 5, WHITE)
    cv.rect(poles[1] + 2, y + 13, 16, 5, NAVY)
    cv.rect(poles[1] + 2, y + 18, 16, 4, RED)
    # USA: stripes + blue canton.
    cv.vline(poles[2], y + 8, h - 20, INK, 2)
    for i in range(4):
        cv.rect(poles[2] + 2, y + 8 + i * 4, 16, 2, RED if i % 2 == 0 else WHITE)
    cv.rect(poles[2] + 2, y + 8, 8, 8, NAVY)
    cv.disc(poles[2] + 5, y + 12, 2, WHITE)


def icon_bridge(cv, x, y, w, h):
    """A bridge with its middle span broken away."""
    cv.rect(x, y, w, h, SKY)
    cv.rect(x, y + h - 18, w, 18, SEA)
    for i in range(4):
        cv.rect(x + 6 + i * 18, y + h - 12, 10, 3, WHITE)
    # Towers and deck.
    cv.rect(x + 10, y + 18, 8, 40, INK)
    cv.rect(x + w - 18, y + 18, 8, 40, INK)
    cv.rect(x + 6, y + 34, w // 2 - 14, 6, INK)
    cv.rect(x + w // 2 + 8, y + 34, w // 2 - 14, 6, INK)
    # Broken span falling.
    cv.line(x + w // 2 - 6, y + 40, x + w // 2 + 8, y + 54, INK, 4)
    # Burst at the break.
    cv.starburst(x + w // 2, y + 30, 12, ORANGE, rays=8)
    cv.starburst(x + w // 2, y + 30, 6, RED, rays=8)


def icon_ballot(cv, x, y, w, h):
    """Ballot box with a paper going in and a check mark."""
    cv.rect(x, y, w, h, LIGHT_PANEL)
    cv.rect(x + 10, y + 26, w - 20, h - 36, NAVY)
    cv.rect(x + 14, y + 22, w - 28, 6, NAVY)
    cv.rect(x + w // 2 - 10, y + 23, 20, 3, WHITE)
    # Ballot paper sliding in.
    cv.line(x + w // 2 - 4, y + 8, x + w // 2 + 4, y + 24, INK, 2)
    cv.rect(x + w // 2 - 8, y + 6, 12, 16, WHITE)
    cv.border(x + w // 2 - 8, y + 6, 12, 16, INK, 1)
    # Check mark on the box.
    cv.line(x + 18, y + 42, x + 26, y + 50, GOLD, 3)
    cv.line(x + 26, y + 50, x + 42, y + 32, GOLD, 3)


def icon_virus(cv, x, y, w, h):
    """Spiked virus particle."""
    cv.rect(x, y, w, h, LIGHT_PINK)
    cx, cy = x + w // 2, y + h // 2
    for k in range(10):
        ang = 2 * math.pi * k / 10
        ex = cx + int(24 * math.cos(ang))
        ey = cy + int(24 * math.sin(ang))
        cv.line(cx, cy, ex, ey, RED, 2)
        cv.disc(ex, ey, 3, RED)
    cv.disc(cx, cy, 15, RED)
    cv.disc(cx - 5, cy - 4, 3, WHITE)
    cv.disc(cx + 5, cy + 4, 3, WHITE)
    cv.disc(cx + 4, cy - 6, 2, WHITE)


def icon_voyager(cv, x, y, w, h):
    """Spacecraft with dish antenna, stars and a dotted trajectory."""
    cv.rect(x, y, w, h, NAVY_DARK)
    for sx, sy in ((8, 8), (w - 10, 12), (12, h - 12), (w - 8, h - 8), (w // 2, 6)):
        cv.rect(x + sx - 1, y + sy - 1, 3, 3, WHITE)
    # Dotted trajectory.
    for i in range(5):
        cv.disc(x + 8 + i * 9, y + h - 14 - i * 7, 2, GOLD)
    # Dish + body.
    cx, cy = x + w // 2 + 6, y + h // 2 - 2
    cv.triangle(cx - 14, cy - 10, cx + 12, cy - 2, cx - 14, cy + 8, GOLD)
    cv.disc(cx + 2, cy, 5, WHITE)
    cv.line(cx + 2, cy, cx + 16, cy - 14, WHITE, 2)
    cv.disc(cx + 16, cy - 14, 2, WHITE)


ICONS = {
    'gulf': icon_gulf,
    'summit': icon_summit,
    'bridge': icon_bridge,
    'ballot': icon_ballot,
    'virus': icon_virus,
    'voyager': icon_voyager,
}


# --- PNG encoding -----------------------------------------------------------
def png_chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    ihdr = struct.pack('>IIBBBBB', canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for yy in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.buf[yy * stride:(yy + 1) * stride]
    return (
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(b'IHDR', ihdr)
        + png_chunk(b'IDAT', zlib.compress(bytes(raw), 9))
        + png_chunk(b'IEND', b'')
    )


# --- Layout -----------------------------------------------------------------
def render(data):
    cv = Canvas(W, H, PAPER)

    # Masthead: title, rules, and the date the image sums up.
    cv.text(W // 2, 26, 6, INK, data['masthead'], align='center')
    cv.hline(24, 84, W - 48, INK, 3)
    cv.text(W // 2, 94, 3, RED, data['date_label'], align='center')
    cv.hline(24, 130, W - 48, RED, 5)

    # Lead story: full-width panel, illustration left, text right.
    lead = data['lead']
    cv.rect(24, 148, 976, 272, WHITE)
    cv.border(24, 148, 976, 272, INK, 3)
    ICONS[lead['icon']](cv, 28, 152, 360, 264)
    cv.border(28, 152, 360, 264, INK, 2)
    cv.text(412, 168, 2, RED, lead['kicker'])
    cv.para(412, 196, 576, 4, INK, lead['headline'], leading=34)
    cv.para(412, 312, 576, 2, INK, lead['summary'], leading=17)

    # Row 2: two half-width cards.
    for i, story in enumerate(data['row2']):
        cx = 24 + i * (478 + 20)
        cy = 436
        cv.rect(cx, cy, 478, 196, WHITE)
        cv.border(cx, cy, 478, 196, INK, 2)
        ICONS[story['icon']](cv, cx + 10, cy + 10, 76, 76)
        cv.border(cx + 10, cy + 10, 76, 76, INK, 1)
        cv.text(cx + 98, cy + 14, 2, RED, story['kicker'])
        cv.para(cx + 98, cy + 36, 368, 3, INK, story['headline'], leading=24)
        cv.para(cx + 12, cy + 112, 454, 2, INK, story['summary'], leading=17)

    # Row 3: three third-width cards.
    for i, story in enumerate(data['row3']):
        cx = 24 + i * (312 + 20)
        cy = 648
        cv.rect(cx, cy, 312, 204, WHITE)
        cv.border(cx, cy, 312, 204, INK, 2)
        ICONS[story['icon']](cv, cx + 10, cy + 10, 56, 56)
        cv.border(cx + 10, cy + 10, 56, 56, INK, 1)
        cv.text(cx + 76, cy + 12, 2, RED, story['kicker'])
        cv.para(cx + 76, cy + 32, 226, 2, INK, story['headline'], leading=17, max_lines=3)
        cv.para(cx + 12, cy + 84, 288, 2, INK, story['summary'], leading=17, max_lines=4)

    # Footer: also-today ticker, markets, and the date note.
    cv.hline(24, 868, W - 48, INK, 3)
    cv.text(24, 880, 2, RED, 'ALSO TODAY')
    for i, item in enumerate(data['also']):
        ix = 24 + (i % 2) * 500
        iy = 904 + (i // 2) * 22
        cv.rect(ix, iy + 3, 8, 8, RED)
        cv.text(ix + 14, iy, 2, INK, item)
    cv.text(W // 2, 952, 2, NAVY, data['markets'], align='center')
    cv.text(W // 2, 976, 2, GRAY, data['footer_note'], align='center')

    return cv


def main():
    here = Path(__file__).resolve().parent
    data = json.loads((here / 'news.json').read_text(encoding='utf-8'))
    canvas = render(data)
    out_dir = Path(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output'))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'entry.png').write_bytes(encode_png(canvas))


if __name__ == '__main__':
    main()
