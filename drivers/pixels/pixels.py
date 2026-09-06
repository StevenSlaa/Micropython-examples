# Colour layer for WS2812B / SK6812 addressable LEDs.
# Wraps the built-in `neopixel` module, which handles the wire protocol already.

from neopixel import NeoPixel


def gamma_table(gamma=2.6, brightness=1.0):
    """256 byte lookup folding gamma correction and a 0..1 brightness scale."""
    top = 255.0 * min(max(brightness, 0.0), 1.0)
    return bytes(int((i / 255.0) ** gamma * top + 0.5) for i in range(256))


def hsv(hue, saturation=1.0, value=1.0):
    """Hue 0..1 around the colour wheel to an (r, g, b) tuple."""
    hue = (hue % 1.0) * 6.0
    sector = int(hue)
    fraction = hue - sector
    p = value * (1.0 - saturation)
    q = value * (1.0 - saturation * fraction)
    t = value * (1.0 - saturation * (1.0 - fraction))
    r, g, b = (
        (value, t, p),
        (q, value, p),
        (p, value, t),
        (p, q, value),
        (t, p, value),
        (value, p, q),
    )[sector]
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


class Pixels:
    """An addressable LED strip with live brightness, gamma, and RGBW support.

    bpp=3 drives WS2812B/WS2812/WS2811 (GRB), bpp=4 drives SK6812 RGBW (GRBW).
    Colours you set are kept unmodified; brightness and gamma are applied in write(),
    so changing either updates the whole strip on the next write.
    """

    def __init__(self, pin, n, bpp=3, brightness=1.0, gamma=2.6, timing=1, auto_white=False):
        self._strip = NeoPixel(pin, n, bpp, timing)
        self.n = n
        self.bpp = bpp
        self.buf = bytearray(n * bpp)
        # SK6812 only: fold the shared part of r, g, b into the white LED. Cleaner
        # whites and less current, but a visible hue shift on some strips, so opt in.
        self.auto_white = auto_white and bpp == 4
        self._gamma = gamma
        self.brightness = brightness

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = min(max(value, 0.0), 1.0)
        self._lut = gamma_table(self._gamma, self._brightness)

    @property
    def gamma(self):
        return self._gamma

    @gamma.setter
    def gamma(self, value):
        self._gamma = value
        self._lut = gamma_table(value, self._brightness)

    def _pack(self, colour):
        if self.bpp == 4 and len(colour) == 3:
            white = min(colour) if self.auto_white else 0
            return (colour[0] - white, colour[1] - white, colour[2] - white, white)
        return colour

    def __len__(self):
        return self.n

    def __setitem__(self, i, colour):
        colour = self._pack(colour)
        offset = (i % self.n) * self.bpp
        for channel in range(self.bpp):
            self.buf[offset + channel] = colour[channel]

    def __getitem__(self, i):
        offset = (i % self.n) * self.bpp
        return tuple(self.buf[offset + channel] for channel in range(self.bpp))

    def fill(self, colour):
        colour = self._pack(colour)
        buf, bpp, size = self.buf, self.bpp, len(self.buf)
        for channel in range(bpp):
            value = colour[channel]
            index = channel
            while index < size:
                buf[index] = value
                index += bpp

    def write(self):
        # ponytail: per-pixel Python loop, a few ms for a couple of hundred LEDs.
        # Fast enough for animation at this length; use a PIO driver if you need more.
        lut, buf, bpp, strip = self._lut, self.buf, self.bpp, self._strip
        for i in range(self.n):
            offset = i * bpp
            strip[i] = tuple(lut[buf[offset + channel]] for channel in range(bpp))
        strip.write()
