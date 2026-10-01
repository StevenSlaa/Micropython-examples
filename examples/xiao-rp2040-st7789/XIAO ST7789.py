# A 240x240 ST7789 colour display on a Seeed XIAO RP2040.
#
# Four scenes, on a loop: a title card, a spinning 3D cube, a warp-speed starfield and a zoom
# into the Mandelbrot set that ends in colour cycling. The animations are drawn into one framebuf
# in RAM and sent to the display in a single blit: drawing through the driver pixel by pixel
# costs an SPI transaction per pixel, and is far too slow to animate.
#
# Three things make it fast enough to be smooth:
# - The CPU runs at 200MHz, the RP2040's rated maximum, instead of 125MHz.
# - SPI runs at 50MHz instead of 24MHz: see the clock note below. A full frame takes 22ms.
# - The Mandelbrot is fixed-point maths in a viper function, compiled to machine code, which is
#   about 30 times faster than the same thing in plain Python, and it runs on both cores.
# The animations also move by the clock, not by the frame, so a slow frame does not make them
# stutter or slow down.

import machine
from machine import Pin, SPI, mem32
from time import sleep_ms, ticks_ms, ticks_diff
from math import sin, cos
from random import randint
import framebuf
import gc
import micropython
import _thread
import st7789py as st7789

# Configuration
# The XIAO labels are in brackets; MicroPython wants the GPIO numbers.
sck_pin = 2         # (D8) SPI0 SCK
mosi_pin = 3        # (D10) SPI0 TX
dc_pin = 26         # (D0)
reset_pin = 27      # (D1)
cs_pin = 28         # (D2) set to None if your module has no CS pin
backlight_pin = 29  # (D3)
scene_ms = 10000    # how long each animation runs
cpu_hz = 200_000_000
spi_divider = 4     # SPI clock = cpu_hz / spi_divider. 4 is 50MHz; use 6 or 8 if you see noise.

width = 240
height = 240

# The SPI clock comes from the peripheral clock, which MicroPython leaves at 48MHz, so SPI tops
# out at 24MHz whatever baudrate is asked for. Running the peripheral clock from the CPU clock
# lifts that. MicroPython does not know about the change and still divides 48MHz when it works
# out the baudrate, so the baudrate passed is the one that gives the right divider from 48MHz.
# The UART also runs from this clock: its baudrates are wrong after this, which does not matter
# here because nothing uses it (the REPL is on USB).
machine.freq(cpu_hz)
_CLK_PERI_CTRL = 0x40008048
mem32[_CLK_PERI_CTRL] = 0        # stop it, and select clk_sys as its source
sleep_ms(1)
mem32[_CLK_PERI_CTRL] = 1 << 11  # start it again

# SPI mode 0 or 3 both work on a module with CS; mode 2 (polarity=1, phase=0) leaves it blank.
# A module without CS needs mode 3: polarity=1, phase=1.
spi = SPI(0, baudrate=48_000_000 // spi_divider, polarity=0, phase=0,
          sck=Pin(sck_pin), mosi=Pin(mosi_pin))
display = st7789.ST7789(
    spi, width, height,
    reset=Pin(reset_pin, Pin.OUT), dc=Pin(dc_pin, Pin.OUT),
    cs=Pin(cs_pin, Pin.OUT) if cs_pin is not None else None,
    backlight=Pin(backlight_pin, Pin.OUT))

# The big buffers are allocated once at the start while the heap is still in one piece: asked for
# later they may not find a gap that big. The screen is 240 x 240 x 2 bytes, 112KB, and the
# Mandelbrot keeps one byte per pixel of iteration counts, 56KB, so it can recolour without
# recomputing.
gc.collect()
buffer = bytearray(width * height * 2)
counts = bytearray(width * height)
screen = framebuf.FrameBuffer(buffer, width, height, framebuf.RGB565)


def rgb(r, g, b):
    # framebuf stores RGB565 little-endian and the ST7789 reads it big-endian, so swap the
    # bytes here and every colour drawn into the buffer arrives the right way round.
    c = st7789.color565(r, g, b)
    return ((c & 0xFF) << 8) | (c >> 8)


def hue(h):
    # 0..255 round the colour wheel, fully saturated.
    h %= 256
    x = (h % 85) * 3
    if h < 85:
        return 255 - x, x, 0
    if h < 170:
        return 0, 255 - x, x
    return x, 0, 255 - x


def present():
    display.blit_buffer(buffer, 0, 0, width, height)


def big_text(text, x, y, colour, scale):
    # framebuf's font is 8x8 only, so draw into a one-line scratch buffer and blow each pixel
    # up. The driver's 16x32 font would do, but it costs 67KB of RAM the screen buffer needs.
    w = len(text) * 8
    line = framebuf.FrameBuffer(bytearray(w), w, 8, framebuf.MONO_HLSB)
    line.text(text, 0, 0, 1)
    for py in range(8):
        for px in range(w):
            if line.pixel(px, py):
                screen.fill_rect(x + px * scale, y + py * scale, scale, scale, colour)


def title():
    for y in range(height):
        screen.hline(0, y, width, rgb(*hue(y)))
    screen.fill_rect(16, 64, 208, 112, 0)
    big_text("XIAO", 56, 76, rgb(255, 255, 255), 4)
    big_text("RP2040", 72, 118, rgb(0, 255, 255), 2)
    big_text("ST7789 240x240", 64, 148, rgb(255, 200, 0), 1)
    present()
    sleep_ms(3000)


def cube():
    points = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    # Pairs of corners one bit apart are the 12 edges.
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8) if bin(a ^ b).count("1") == 1]
    white = rgb(255, 255, 255)
    started = last = ticks_ms()
    while True:
        now = ticks_ms()
        t = ticks_diff(now, started)
        if t >= scene_ms:
            break
        angle = t * 0.0016  # radians per millisecond: the speed is the same at any frame rate
        sx, cx, sy, cy = sin(angle), cos(angle), sin(angle * 0.7), cos(angle * 0.7)
        # Breathes in and out a little, to show off the frame rate.
        zoom = 200 + 30 * sin(angle * 1.3)
        projected = []
        for x, y, z in points:
            y, z = y * cx - z * sx, y * sx + z * cx
            x, z = x * cy + z * sy, -x * sy + z * cy
            scale = zoom / (z + 4)
            projected.append((int(120 + x * scale), int(120 + y * scale)))

        screen.fill(0)
        for i, (a, b) in enumerate(edges):
            colour = rgb(*hue(i * 21 + t // 12))
            (x0, y0), (x1, y1) = projected[a], projected[b]
            # Three lines side by side for a line thick enough to read at 240 pixels.
            screen.line(x0, y0, x1, y1, colour)
            screen.line(x0 + 1, y0, x1 + 1, y1, colour)
            screen.line(x0, y0 + 1, x1, y1 + 1, colour)
        for x, y in projected:
            screen.ellipse(x, y, 4, 4, white, True)
        screen.text("3D cube  %d fps" % (1000 // max(1, ticks_diff(now, last))), 4, 4, white)
        last = now
        present()


@micropython.native
def _draw_stars(stars, move, star_colours, trail_colours):
    # Native code: twice as fast as plain Python, and with 140 stars this loop is the frame.
    for star in stars:
        star[2] -= move
        x, y, z = star
        if z <= 0:
            star[0], star[1], star[2] = randint(-1000, 1000), randint(-1000, 1000), 1000
            continue
        px = 120 + x * 100 // z
        py = 120 + y * 100 // z
        if not (0 <= px < 240 and 0 <= py < 240):
            star[2] = 0  # off the edge: respawn it next frame
            continue
        # Nearer stars are bigger, brighter and leave a streak back towards the centre.
        near = (1000 - z) >> 6  # 0..15
        size = 1 + near // 5
        tx = 120 + x * 100 // (z + 80)
        ty = 120 + y * 100 // (z + 80)
        screen.line(tx, ty, px, py, trail_colours[near])
        screen.fill_rect(px, py, size, size, star_colours[near])


def starfield():
    count = 140
    stars = [[randint(-1000, 1000), randint(-1000, 1000), randint(1, 1000)] for _ in range(count)]
    # 16 brightness steps, worked out once rather than per star per frame.
    levels = [60 + n * 13 for n in range(16)]
    star_colours = [rgb(v, v, 255 if n > 7 else v) for n, v in enumerate(levels)]
    trail_colours = [rgb(v // 3, v // 3, v // 2) for v in levels]
    white = rgb(255, 255, 255)
    started = last = ticks_ms()
    while True:
        now = ticks_ms()
        if ticks_diff(now, started) >= scene_ms:
            break
        # Distance travelled this frame, from the time it took: steady speed at any frame rate.
        move = ticks_diff(now, last) * 3 // 4
        last = now
        screen.fill(0)
        _draw_stars(stars, move, star_colours, trail_colours)
        screen.text("warp speed", 4, 4, white)
        present()


# Fixed point with 14 fractional bits: 16384 is 1.0. Viper only does fast maths on integers.
_ONE = 1 << 14


@micropython.viper
def mandelbrot_rows(out: ptr8, left: int, top: int, step: int, block: int, first: int,
                    every: int):
    # Iteration counts for the 240x240 view into `out`. Only one pixel in every `block` x
    # `block` square is computed and copied across the square: block 3 is nine times faster.
    # Rows `first`, `first + every`, ... so the two cores can take alternate rows: the
    # interesting part of the picture is then always shared evenly between them.
    four = 4 << 14
    y = first * block
    while y < 240:
        ci = top + y * step
        x = 0
        while x < 240:
            cr = left + x * step
            zr = 0
            zi = 0
            zr2 = 0
            zi2 = 0
            n = 0
            while n < 64:
                zi = ((zr * zi) >> 13) + ci
                zr = zr2 - zi2 + cr
                n += 1
                # Squared at 13 bits rather than 14: z can reach about 6.3 on the step that
                # escapes, and squared at 14 bits that overflows 32 bits.
                a = zr >> 1
                b = zi >> 1
                zr2 = (a * a) >> 12
                zi2 = (b * b) >> 12
                if zr2 + zi2 > four:
                    break
            dy = 0
            while dy < block and y + dy < 240:
                dx = 0
                while dx < block and x + dx < 240:
                    out[(y + dy) * 240 + x + dx] = n
                    dx += 1
                dy += 1
            x += block
        y += block * every


def _core1(job, done, out, rows):
    # Runs on the second core for good, waiting for a view to compute the odd rows of.
    # ponytail: busy-waits, so core 1 is always at 100%; a lock would let it idle if power matters.
    while True:
        view = job[0]
        if view is None:
            continue
        job[0] = None
        rows(out, view[0], view[1], view[2], view[3], 1, 2)
        done[0] = True


_job = [None]
_done = [False]
# The lists and the function are passed in, not looked up as globals: a thread started from
# a script run by mpremote does not see that script's globals.
_thread.start_new_thread(_core1, (_job, _done, counts, mandelbrot_rows))


def mandelbrot_counts(cx, cy, w, block):
    # Both cores: this one takes the even rows while the other takes the odd ones.
    step = int(w / 240 * _ONE)
    view = (int((cx - w / 2) * _ONE), int((cy - w / 2) * _ONE), step, block)
    _done[0] = False
    _job[0] = view
    mandelbrot_rows(counts, view[0], view[1], view[2], view[3], 0, 2)
    while not _done[0]:
        pass


@micropython.viper
def colourise(out: ptr16, counts_in: ptr8, palette: ptr16, shift: int):
    # Count to colour through a 64 entry palette, rotated by `shift`. The inside of the set
    # (count 64) stays black.
    i = 0
    while i < 57600:
        n = counts_in[i]
        if n < 64:
            out[i] = palette[(n + shift) & 63]
        else:
            out[i] = 0
        i += 1


def mandelbrot():
    palette = bytearray(2 * 64)
    for n in range(64):
        c = rgb(*hue(n * 4))
        palette[2 * n] = c & 0xFF
        palette[2 * n + 1] = c >> 8
    white = rgb(255, 255, 255)

    # Zoom from the whole set into Seahorse Valley, the centre gliding across as the view
    # narrows. Each frame is a fixed fraction narrower, so the zoom looks steady.
    target_x, target_y = -0.743643887, 0.131825904
    start_x, start_y, start_w = -0.75, 0.0, 3.0
    # 100x: deeper than this the 14 bit fixed point step falls below 2, and it turns blocky.
    end_w = 0.03
    w = start_w
    shift = 0
    while w > end_w:
        f = (w - end_w) / (start_w - end_w)
        cx = target_x + (start_x - target_x) * f
        cy = target_y + (start_y - target_y) * f
        mandelbrot_counts(cx, cy, w, 3)
        colourise(buffer, counts, palette, shift)
        screen.text("Mandelbrot  x%d" % int(start_w / w), 4, 4, white)
        present()
        w *= 0.94
        shift += 1

    # The last view at full resolution, then cycle the colours through it: no recomputing, so
    # it runs at the full frame rate.
    mandelbrot_counts(cx, cy, w, 1)
    started = ticks_ms()
    while ticks_diff(ticks_ms(), started) < 5000:
        colourise(buffer, counts, palette, shift)
        present()
        shift += 1


while True:
    for scene in (title, cube, starfield, mandelbrot):
        scene()
