# Talks to Meshtastic devices through an SX127x radio: text messages on a channel, and node names.
# The radio settings, packet header, encryption and the few protobuf messages it needs follow the
# Meshtastic firmware, so phones and devices running Meshtastic see this board as a node.
# Protocol: https://meshtastic.org/docs/overview/mesh-algo/ (a separate implementation; none of the
# GPL-3.0 firmware code is copied)

from cryptolib import aes
from os import urandom
from struct import pack, unpack

BROADCAST = 0xFFFFFFFF
TEXT = 1  # portnum TEXT_MESSAGE_APP
NODEINFO = 4  # portnum NODEINFO_APP

# The key every Meshtastic device ships with for its default channel, the one called "AQ==".
DEFAULT_KEY = bytes((0xD4, 0xF1, 0xBB, 0x3A, 0x20, 0x29, 0x07, 0x59,
                     0xF0, 0xBC, 0xFF, 0xAB, 0xCF, 0x4E, 0x69, 0x01))

# Modem presets: bandwidth, spreading factor, coding rate. The default channel is named after its
# preset, and the name decides the frequency, so both ends only need the same preset and region.
PRESETS = {
    "LongFast": (250_000, 11, 5),
    "LongModerate": (125_000, 11, 8),
    "LongSlow": (125_000, 12, 8),
    "MediumFast": (250_000, 9, 5),
    "MediumSlow": (250_000, 10, 5),
    "ShortFast": (250_000, 7, 5),
    "ShortSlow": (250_000, 8, 5),
}

# The band each region may use, in Hz. ponytail: the regions an SX1276/SX1278 can reach and that
# have LoRa boards sold for them; add others from the Meshtastic firmware's RadioInterface.cpp.
REGIONS = {
    "EU_868": (869_400_000, 869_650_000),
    "EU_433": (433_000_000, 434_000_000),
    "US": (902_000_000, 928_000_000),
    "ANZ": (915_000_000, 928_000_000),
}


def frequency(region, preset, channel=None):
    """The centre frequency Meshtastic picks: a hash of the channel name chooses a slot in the band."""
    start, end = REGIONS[region]
    bandwidth = PRESETS[preset][0]
    name = channel or preset
    djb2 = 5381
    for char in name.encode():
        djb2 = (djb2 * 33 + char) & 0xFFFFFFFF
    slot = djb2 % ((end - start) // bandwidth)
    return start + bandwidth // 2 + slot * bandwidth


def channel_hash(name, key):
    """The byte in each packet saying which channel it is on: the name and key XORed together."""
    result = 0
    for byte in name.encode() + key:
        result ^= byte
    return result


def _crypt(key, packet_id, sender, data):
    """AES-CTR, which encrypts and decrypts alike. The nonce is the packet ID and the sender."""
    cipher = aes(key, 1)
    out = bytearray(data)
    for block in range(0, len(data), 16):
        counter = pack("<QI", packet_id, sender) + pack(">I", block // 16)
        for i, byte in enumerate(cipher.encrypt(counter)[:len(data) - block]):
            out[block + i] ^= byte
    return bytes(out)


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if not value:
            out.append(byte)
            return bytes(out)
        out.append(byte | 0x80)


def _field(number, value):
    """One protobuf field: a number as a varint, text or bytes as length-delimited."""
    if isinstance(value, int):
        return _varint(number << 3) + _varint(value)
    if isinstance(value, str):
        value = value.encode()
    return _varint(number << 3 | 2) + _varint(len(value)) + value


def _read_varint(data, i):
    value = shift = 0
    while True:
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, i


def _parse(data):
    """The fields of a protobuf message as {number: value}. Enough for Data and User."""
    fields = {}
    i = 0
    while i < len(data):
        key, i = _read_varint(data, i)
        kind = key & 7
        if kind == 0:
            value, i = _read_varint(data, i)
        elif kind == 2:
            length, i = _read_varint(data, i)
            value = bytes(data[i:i + length])
            i += length
        elif kind in (1, 5):
            size = 8 if kind == 1 else 4
            value = bytes(data[i:i + size])
            i += size
        else:
            raise ValueError("unsupported protobuf field")
        fields[key >> 3] = value
    return fields


class Meshtastic:
    """A Meshtastic node on `radio`, an SX127x. `node_id` is 32 bits, usually from the MAC address.

    `long_name` and `short_name` (up to 4 characters) are how other nodes list this one. The
    region, preset, channel name and key must match the other devices; the defaults are
    Meshtastic's own out of the box.
    """

    def __init__(self, radio, node_id, long_name, short_name, region="EU_868", preset="LongFast",
                 channel=None, key=DEFAULT_KEY, hop_limit=3):
        bandwidth, spreading_factor, coding_rate = PRESETS[preset]
        self.radio = radio
        self.node_id = node_id
        self.long_name = long_name
        self.short_name = short_name[:4]
        self.key = key
        self.channel = channel_hash(channel or preset, key)
        self.hop_limit = hop_limit
        self.names = {}  # node ID to long name, from the node info others send
        self._seen = []
        radio.configure(frequency=frequency(region, preset, channel), bandwidth=bandwidth,
                        spreading_factor=spreading_factor, coding_rate=coding_rate,
                        sync_word=0x2B, preamble_length=16, crc=True, invert_iq=False)
        radio.receive()

    def name(self, node_id):
        """A node's long name if it has told us, otherwise the !1234abcd form Meshtastic shows."""
        return self.names.get(node_id) or "!%08x" % node_id

    def _send(self, port, payload, to=BROADCAST):
        packet_id = int.from_bytes(urandom(4), "little")
        # Flags: hops left in the low 3 bits, hops it started with in the top 3.
        flags = self.hop_limit | self.hop_limit << 5
        header = pack("<IIIBBBB", to, self.node_id, packet_id, flags, self.channel, 0,
                      self.node_id & 0xFF)
        data = _field(1, port) + _field(2, payload)
        self._remember(self.node_id, packet_id)
        self.radio.send(header + _crypt(self.key, packet_id, self.node_id, data))
        return packet_id

    def send_text(self, text):
        """Sends `text` to everyone on the channel. Meshtastic caps a message near 200 bytes."""
        payload = text.encode()
        if not 0 < len(payload) <= 200:
            raise ValueError("a message is 1 to 200 bytes")
        return self._send(TEXT, payload)

    def send_node_info(self):
        """Tells the mesh this node's names, so apps list it by name rather than by number."""
        # User: id, long name, short name, and hardware model 3, the T-LoRa V2.1-1.6.
        user = (_field(1, "!%08x" % self.node_id) + _field(2, self.long_name) +
                _field(3, self.short_name) + _field(5, 3))
        return self._send(NODEINFO, user)

    def _remember(self, sender, packet_id):
        """False for a packet already seen: other nodes repeat everything they hear."""
        key = (sender, packet_id)
        if key in self._seen:
            return False
        self._seen = self._seen[-31:] + [key]
        return True

    def recv(self):
        """The next text message as (sender ID, text), or None. Node info is taken in quietly."""
        packet = self.radio.recv()
        if not packet or len(packet) < 17:
            return None
        to, sender, packet_id, _, channel = unpack("<IIIBB", packet[:14])
        if (channel != self.channel or to not in (BROADCAST, self.node_id)
                or not self._remember(sender, packet_id)):
            return None
        try:
            data = _parse(_crypt(self.key, packet_id, sender, packet[16:]))
            port, payload = data.get(1), data.get(2, b"")
            if port == NODEINFO:
                self.names[sender] = _parse(payload).get(2, b"").decode()
            elif port == TEXT:
                return sender, payload.decode()
        except (ValueError, IndexError, UnicodeError):
            pass  # another channel with the same hash byte, or a packet damaged on the way
        return None
