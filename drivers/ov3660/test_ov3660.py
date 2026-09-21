# Run with: python3 -B drivers/ov3660/test_ov3660.py
# A fake `camera` module standing in for the firmware's. What is worth pinning down here is the
# pin map, because a data line in the wrong order gives a picture that is noise rather than an
# error, and there is no way to tell that apart from a bad sensor by looking at the board.
import sys, types


class _Camera:
    def __init__(self, **settings):
        self.settings = settings
        self.calls = []

    def init(self):
        self.calls.append(("init",))

    def set_vflip(self, value):
        self.calls.append(("vflip", value))

    def set_brightness(self, value):
        self.calls.append(("brightness", value))

    def set_saturation(self, value):
        self.calls.append(("saturation", value))


made = []


def _make(**settings):
    made.append(_Camera(**settings))
    return made[-1]


sys.modules["camera"] = types.SimpleNamespace(
    Camera=_make,
    FrameSize=types.SimpleNamespace(SVGA="svga", QVGA="qvga", QXGA="qxga"),
    PixelFormat=types.SimpleNamespace(JPEG="jpeg", RGB565="rgb565"),
    GrabMode=types.SimpleNamespace(WHEN_EMPTY=0, LATEST=1),
)
import ov3660  # noqa: E402

# The pins, as Seeed wires them. D0 is Y2 and D7 is Y9, which is the order the firmware reads
# the list in; written the other way round the bits of every pixel come out reversed.
cam = ov3660.camera()
assert cam.settings["data_pins"] == [15, 17, 18, 16, 14, 12, 11, 48], cam.settings["data_pins"]
assert cam.settings["pclk_pin"] == 13 and cam.settings["xclk_pin"] == 10
assert cam.settings["vsync_pin"] == 38 and cam.settings["href_pin"] == 47
assert cam.settings["sda_pin"] == 40 and cam.settings["scl_pin"] == 39
assert cam.settings["reset_pin"] == -1 and cam.settings["powerdown_pin"] == -1

# It is started before it is handed back, and the OV3660's corrections are applied after that:
# setting the sensor up before it exists is the mistake this order prevents.
assert cam.calls == [("init",), ("vflip", True), ("brightness", 1), ("saturation", -2)], cam.calls
assert cam.settings["frame_size"] == "svga" and cam.settings["pixel_format"] == "jpeg"

# The knobs are knobs. Real light is not the light the defaults were picked in.
cam = ov3660.camera(frame_size=ov3660.FrameSize.QXGA, jpeg_quality=4, brightness=-1, vflip=False)
assert cam.settings["frame_size"] == "qxga" and cam.settings["jpeg_quality"] == 4
assert ("brightness", -1) in cam.calls and ("vflip", False) in cam.calls

# None leaves the sensor's own default in place rather than writing a value over it.
cam = ov3660.camera(vflip=None, brightness=None, saturation=None)
assert cam.calls == [("init",)], cam.calls

# Anything the firmware understands and this module does not gets passed along untouched.
cam = ov3660.camera(fb_count=2, xclk_freq=16000000, grab_mode=ov3660.GrabMode.LATEST)
assert cam.settings["fb_count"] == 2 and cam.settings["xclk_freq"] == 16000000
assert cam.settings["grab_mode"] == 1

# A different board with the same sensor brings its own pins, and keeps the corrections.
other = dict(ov3660.XIAO_ESP32S3_SENSE, xclk_pin=21)
cam = ov3660.camera(pins=other)
assert cam.settings["xclk_pin"] == 21
assert ("vflip", True) in cam.calls
assert ov3660.XIAO_ESP32S3_SENSE["xclk_pin"] == 10, "the board's own map is not edited in place"

print("ov3660: ok")
