# Run with: python3 -B drivers/meshtastic/test_meshtastic.py
# Checks frequencies, encryption and packets off-board, with openssl standing in for the
# firmware's AES and a fake radio.
import struct, subprocess, sys, types


def _openssl(key, data, mode="ecb", iv=None):
    command = ["openssl", "enc", "-aes-128-" + mode, "-nopad", "-K", key.hex()]
    if iv:
        command += ["-iv", iv.hex()]
    return subprocess.run(command, input=bytes(data), capture_output=True, check=True).stdout


class _AES:
    def __init__(self, key, mode):
        assert mode == 1, "ECB"
        self.key = key

    def encrypt(self, data):
        return _openssl(self.key, data)


sys.modules["cryptolib"] = types.SimpleNamespace(aes=_AES)
from meshtastic import (DEFAULT_KEY, Meshtastic, _crypt, _field, _parse,  # noqa: E402
                        channel_hash, frequency)


class _Radio:
    def __init__(self):
        self.sent, self.incoming, self.settings = [], [], {}

    def configure(self, **settings):
        self.settings.update(settings)

    def receive(self):
        pass

    def send(self, packet):
        self.sent.append(packet)

    def recv(self):
        return self.incoming.pop(0) if self.incoming else None


# The LongFast frequencies Meshtastic users know by heart for each region.
assert frequency("EU_868", "LongFast") == 869_525_000
assert frequency("US", "LongFast") == 906_875_000
assert frequency("EU_433", "LongFast") == 433_875_000
assert frequency("ANZ", "LongFast") == 919_875_000
assert channel_hash("LongFast", DEFAULT_KEY) == 8, "the default channel is hash 8"

# CTR: the counter block is the packet ID and sender, with a block count in the last four bytes,
# which is what openssl's own CTR mode does from the same starting block.
message = bytes(range(40))
nonce = struct.pack("<QI", 0x12345678, 0xA3F2B7C4) + bytes(4)
assert _crypt(DEFAULT_KEY, 0x12345678, 0xA3F2B7C4, message) == _openssl(DEFAULT_KEY, message, "ctr", nonce)

assert _field(1, 1) + _field(2, "hi") == bytes.fromhex("080112026869"), "Data for a text"
assert _parse(bytes.fromhex("0801120268694d78563412")) == {1: 1, 2: b"hi", 9: b"\x78\x56\x34\x12"}
assert _parse(_field(2, 300)) == {2: 300}, "multi-byte varints"

radio = _Radio()
me = Meshtastic(radio, 0xA3F2B7C4, "Test board", "TEST5")
assert radio.settings["frequency"] == 869_525_000 and radio.settings["spreading_factor"] == 11
assert radio.settings["bandwidth"] == 250_000 and radio.settings["sync_word"] == 0x2B
assert radio.settings["preamble_length"] == 16 and me.short_name == "TEST"

packet_id = me.send_text("hello mesh")
packet = radio.sent[-1]
to, sender, pid, flags, channel, next_hop, relay = struct.unpack("<IIIBBBB", packet[:16])
assert (to, sender, pid) == (0xFFFFFFFF, 0xA3F2B7C4, packet_id), "broadcast from us"
assert flags == 0x63 and channel == 8 and relay == 0xC4, "three hops, default channel"
assert _parse(_crypt(DEFAULT_KEY, pid, sender, packet[16:])) == {1: 1, 2: b"hello mesh"}

# Another node: its name first, then a message, then the same message relayed by a third node.
other = Meshtastic(_Radio(), 0x1B7C0001, "Garden node", "GDN")
other.send_node_info()
other.send_text("hi there")
radio.incoming = other.radio.sent[:] + [other.radio.sent[-1]]
assert me.recv() is None, "node info is taken in quietly"
assert me.name(0x1B7C0001) == "Garden node" and me.name(0x99) == "!00000099"
assert me.recv() == (0x1B7C0001, "hi there")
assert me.recv() is None, "a repeat of the same packet is dropped"

radio.incoming = [packet]
assert me.recv() is None, "our own packet coming back is dropped"
other.send_text("on another channel")
fresh = other.radio.sent[-1]
radio.incoming = [fresh[:13] + b"\x09" + fresh[14:]]
assert me.recv() is None, "another channel is ignored"
radio.incoming = [fresh]
assert me.recv() == (0x1B7C0001, "on another channel"), "the same packet on ours is not"
bad = bytearray(other.radio.sent[0])
bad[8] ^= 1  # another packet ID makes the decryption garbage
radio.incoming = [bytes(bad)]
me.recv()  # must not raise

print("meshtastic: ok")
