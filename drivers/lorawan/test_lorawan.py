# Run with: python3 -B drivers/lorawan/test_lorawan.py
# Checks the packet building and the cryptography off-board, with openssl standing in for the
# firmware's AES and a fake radio that plays the network's part.
import os, subprocess, sys, tempfile, time, types


def _openssl(key, data, decrypt=False):
    command = ["openssl", "enc", "-aes-128-ecb", "-nopad", "-K", key.hex()] + (["-d"] if decrypt else [])
    return subprocess.run(command, input=bytes(data), capture_output=True, check=True).stdout


class _AES:
    def __init__(self, key, mode):
        assert mode == 1, "ECB"
        self.key = key

    def encrypt(self, data):
        return _openssl(self.key, data)


sys.modules["cryptolib"] = types.SimpleNamespace(aes=_AES)
time.sleep_ms = lambda ms: None
time.ticks_ms = lambda: 0
time.ticks_add = lambda a, b: a + b
time.ticks_diff = lambda a, b: a - b
from lorawan import LoRaWAN, _crypt, _mic, _signed  # noqa: E402


class _Radio:
    """Records what was sent, and answers in the receive window listed in `replies`."""

    def __init__(self):
        self.sent = []
        self.replies = []  # one entry per window: bytes, or None for silence
        self.settings = {}
        self.windows = []

    def configure(self, **settings):
        self.settings.update(settings)

    def send(self, packet):
        assert not self.settings.get("invert_iq"), "uplinks go out with normal IQ"
        self.sent.append(bytes(packet))
        self.uplink = dict(self.settings)

    def receive(self):
        assert self.settings["invert_iq"], "downlinks are heard with inverted IQ"
        self.windows.append(dict(self.settings))

    def recv(self, timeout_ms=0):
        return self.replies.pop(0) if self.replies else None

    def sleep(self):
        pass


# AES-CMAC, from the examples in RFC 4493.
key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
message = bytes.fromhex("6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411")
assert _mic(key, b"") == bytes.fromhex("bb1d6929"), "empty message"
assert _mic(key, message[:16]) == bytes.fromhex("070a16b4"), "one whole block"
assert _mic(key, message) == bytes.fromhex("dfa66747"), "a partial last block"

session = os.path.join(tempfile.mkdtemp(), "lorawan.json")
app_key = "2b7e151628aed2a6abf7158809cf4f3c"
radio = _Radio()
device = LoRaWAN(radio, "70B3D57ED0000001", "0000000000000000", app_key, session_file=session)
assert radio.settings["sync_word"] == 0x34 and not device.joined

# Join: the network answers in RX2 with a join accept, encrypted the way a network server does.
app_nonce, net_id, dev_addr = b"\x01\x02\x03", b"\x13\x00\x00", bytes.fromhex("f17dbe49")
accept = app_nonce + net_id + dev_addr + b"\x03\x05"  # RX2 at DR3, RX1 five seconds after
accept_mic = _mic(bytes.fromhex(app_key), b"\x20" + accept)
radio.replies = [None, b"\x20" + _openssl(bytes.fromhex(app_key), accept + accept_mic, decrypt=True)]
assert device.join(), "join accept understood"

request = radio.sent[-1]
assert request[0] == 0x00 and request[9:17] == bytes.fromhex("010000D07ED5B370"), "DevEUI reversed"
assert request[-4:] == _mic(bytes.fromhex(app_key), request[:-4]), "join request signed"
rx1, rx2 = radio.windows
assert rx1["frequency"] == radio.uplink["frequency"], "EU868 answers on the channel it heard"
assert rx1["spreading_factor"] == radio.uplink["spreading_factor"] == 9
assert rx2["frequency"] == 869_525_000 and rx2["spreading_factor"] == 9, "TTN's RX2"
assert device.dev_addr == dev_addr and device.rx1_delay == 5000 and device.rx2_dr == 3
secret = app_nonce + net_id + request[17:19] + bytes(7)
assert device.nwk_skey == _openssl(bytes.fromhex(app_key), b"\x01" + secret), "network key"
assert device.app_skey == _openssl(bytes.fromhex(app_key), b"\x02" + secret), "application key"

# An uplink, checked against the example packet published by the lora-packet project.
device.nwk_skey = bytes.fromhex("44024241ed4ce9a68c6a8bc055233fd3")
device.app_skey = bytes.fromhex("ec925802ae430ca77fd3dd73cb2cc588")
device.fcnt_up = 2
radio.replies = []
assert device.send(b"test") is None, "nothing came back"
assert radio.sent[-1] == bytes.fromhex("40F17DBE4900020001954378762B11FF0D"), radio.sent[-1].hex()
assert device.fcnt_up == 3

# The session survives a reset.
again = LoRaWAN(_Radio(), "70B3D57ED0000001", "0000000000000000", app_key, session_file=session)
assert again.joined and again.fcnt_up == 3 and again.app_skey == device.app_skey, "session restored"
other = LoRaWAN(_Radio(), "70B3D57ED0000002", "0000000000000000", app_key, session_file=session)
assert not other.joined, "another device's session is not used"

# A confirmed downlink on port 5, heard in RX1: returned, and acknowledged by the next uplink.
header = b"\xa0" + dev_addr + b"\x00" + (7).to_bytes(2, "little") + b"\x05"
downlink = header + _crypt(device.app_skey, dev_addr, 7, 1, b"hi")
downlink += _signed(device.nwk_skey, dev_addr, 7, 1, downlink)
radio.replies = [downlink]
assert device.send(b"\x01") == b"hi", "downlink decrypted"
radio.replies = []
device.send(b"\x02")
assert radio.sent[-1][5] == 0x20, "ACK set in the next uplink"
radio.replies = [downlink[:-1] + b"\x00"]
assert device.send(b"\x03") is None, "a bad signature is ignored"

print("lorawan: ok")
