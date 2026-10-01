# A small LoRaWAN 1.0.x end device on top of the sx127x driver: class A, joining over the air
# (OTAA), for The Things Network and other LoRaWAN networks. The session is kept in flash, so a
# reset does not mean joining again.
# Specification: https://resources.lora-alliance.org/technical-specifications/ts001-1-0-4-lorawan-l2-1-0-4-specification

from binascii import hexlify, unhexlify
from cryptolib import aes
from os import urandom
from struct import pack, unpack
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms
import json

# Per region: uplink channels, the RX1 frequency answering each, the downlink bandwidth, the RX2
# frequency and data rate, and the data rate that means SF12 on a downlink.
# ponytail: the three default EU868 channels only, and sub-band 2 in the Americas and Australia,
# which is the one The Things Network uses. Extra channels a network offers are ignored.
REGIONS = {
    "EU868": ((868_100_000, 868_300_000, 868_500_000), (868_100_000, 868_300_000, 868_500_000),
              125_000, 869_525_000, 3, 0),  # RX2 at DR3 (SF9) is TTN's; the standard says DR0
    "US915": (tuple(903_900_000 + 200_000 * n for n in range(8)),
              tuple(923_300_000 + 600_000 * n for n in range(8)), 500_000, 923_300_000, 8, 8),
    "AU915": (tuple(916_800_000 + 200_000 * n for n in range(8)),
              tuple(923_300_000 + 600_000 * n for n in range(8)), 500_000, 923_300_000, 8, 8),
}


def _xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _double(block):
    out = bytearray(16)
    carry = 0
    for i in range(15, -1, -1):
        out[i] = (block[i] << 1 | carry) & 0xFF
        carry = block[i] >> 7
    if carry:
        out[15] ^= 0x87
    return out


def _mic(key, message):
    """The first four bytes of AES-CMAC (RFC 4493), which LoRaWAN signs every packet with."""
    cipher = aes(key, 1)
    subkey = _double(cipher.encrypt(bytes(16)))
    blocks = (len(message) + 15) // 16 or 1
    last = bytearray(message[(blocks - 1) * 16:])
    if len(last) < 16:
        subkey = _double(subkey)
        last += b"\x80" + bytes(15 - len(last))
    state = bytes(16)
    for i in range(blocks - 1):
        state = cipher.encrypt(_xor(state, message[i * 16:i * 16 + 16]))
    return cipher.encrypt(_xor(state, _xor(last, subkey)))[:4]


def _crypt(key, dev_addr, fcnt, downlink, data):
    """Encrypts an uplink's payload, or decrypts a downlink's: the same operation both ways."""
    cipher = aes(key, 1)
    out = bytearray(data)
    for i in range(0, len(data), 16):
        block = bytes((1, 0, 0, 0, 0, downlink)) + dev_addr + pack("<I", fcnt) + bytes((0, i // 16 + 1))
        for j, byte in enumerate(cipher.encrypt(block)[:len(data) - i]):
            out[i + j] ^= byte
    return bytes(out)


def _signed(key, dev_addr, fcnt, downlink, message):
    b0 = bytes((0x49, 0, 0, 0, 0, downlink)) + dev_addr + pack("<I", fcnt) + bytes((0, len(message)))
    return _mic(key, b0 + message)


class LoRaWAN:
    """A LoRaWAN device using `radio`, an SX127x. The EUIs and key are hex, as the console shows.

    `spreading_factor` is the uplink data rate: 7 is short airtime and range, 12 the most range
    (Europe) and 10 the most allowed in the US915 and AU915 plans. The session is saved to
    `session_file`; delete it to join again.
    """

    def __init__(self, radio, dev_eui, join_eui, app_key, region="EU868", spreading_factor=9,
                 session_file="lorawan.json"):
        self.radio = radio
        # The console shows EUIs most significant byte first; the air wants them the other way.
        self.dev_eui = unhexlify(dev_eui)[::-1]
        self.join_eui = unhexlify(join_eui)[::-1]
        self.app_key = unhexlify(app_key)
        self.region = REGIONS[region]
        self.spreading_factor = spreading_factor
        self.session_file = session_file
        self.dev_addr = None
        self._ack = False
        radio.configure(sync_word=0x34)  # public LoRaWAN networks

        try:
            with open(session_file) as f:
                session = json.load(f)
            if unhexlify(session["dev_eui"]) == self.dev_eui and unhexlify(session["app_key"]) == self.app_key:
                self.dev_addr = unhexlify(session["dev_addr"])
                self.nwk_skey = unhexlify(session["nwk_skey"])
                self.app_skey = unhexlify(session["app_skey"])
                self.fcnt_up = session["fcnt_up"]
                self.rx1_delay = session["rx1_delay"]
                self.rx1_offset = session["rx1_offset"]
                self.rx2_dr = session["rx2_dr"]
        except (OSError, ValueError, KeyError):
            pass  # no session yet, or one for another device: join()

    @property
    def joined(self):
        return self.dev_addr is not None

    def join(self):
        """Sends one join request and listens for the answer. True once the network accepts."""
        dev_nonce = urandom(2)
        request = b"\x00" + self.join_eui + self.dev_eui + dev_nonce
        answer = self._exchange(request + _mic(self.app_key, request), 5000, 0, self.region[4])
        if not answer or answer[0] != 0x20 or len(answer) not in (17, 33):
            return False
        # The network encrypts with AES decryption, so encrypting here is what undoes it.
        body = aes(self.app_key, 1).encrypt(answer[1:])
        if _mic(self.app_key, answer[:1] + body[:-4]) != body[-4:]:
            return False

        self.dev_addr = body[6:10]
        self.rx1_offset = body[10] >> 4 & 0x07
        self.rx2_dr = body[10] & 0x0F
        self.rx1_delay = (body[11] & 0x0F or 1) * 1000
        secret = body[:6] + dev_nonce + bytes(7)  # the network's nonce and ID, then this device's
        self.nwk_skey = aes(self.app_key, 1).encrypt(b"\x01" + secret)
        self.app_skey = aes(self.app_key, 1).encrypt(b"\x02" + secret)
        self.fcnt_up = 0
        self._save()
        return True

    def send(self, data, port=1):
        """Sends `data` (bytes) on `port`, 1 to 223. Returns what the network sent back, or None.

        Nothing confirms that the uplink arrived: look in the console to see what came through.
        """
        if not self.joined:
            raise OSError("join() first")
        fcnt = self.fcnt_up
        # FCtrl: acknowledge a confirmed downlink, if the last one asked for that.
        message = (b"\x40" + self.dev_addr + bytes((0x20 if self._ack else 0,)) +
                   pack("<H", fcnt & 0xFFFF) + bytes((port,)) +
                   _crypt(self.app_skey, self.dev_addr, fcnt, 0, data))
        message += _signed(self.nwk_skey, self.dev_addr, fcnt, 0, message)
        self.fcnt_up += 1
        self._ack = False
        # Saved before sending: the network drops an uplink whose counter it has seen before.
        self._save()

        reply = self._exchange(message, self.rx1_delay, self.rx1_offset, self.rx2_dr)
        return self._open(reply) if reply else None

    def _exchange(self, packet, rx1_delay, rx1_offset, rx2_dr):
        """Sends on a random channel, then listens in the two receive windows class A allows."""
        uplinks, rx1_frequencies, bandwidth, rx2_frequency, _, sf12 = self.region
        channel = urandom(1)[0] % len(uplinks)
        radio = self.radio
        radio.configure(frequency=uplinks[channel], bandwidth=125_000,
                        spreading_factor=self.spreading_factor, invert_iq=False)
        radio.send(packet)
        sent = ticks_ms()

        for delay, frequency, sf in ((rx1_delay, rx1_frequencies[channel], min(12, self.spreading_factor + rx1_offset)),
                                     (rx1_delay + 1000, rx2_frequency, 12 - (rx2_dr - sf12))):
            radio.configure(frequency=frequency, bandwidth=bandwidth, spreading_factor=sf,
                            invert_iq=True)
            # Open a little early, and stay long enough to catch the start of a preamble.
            wait = ticks_diff(ticks_add(sent, delay - 20), ticks_ms())
            if wait > 0:
                sleep_ms(wait)
            radio.receive()
            reply = radio.recv(timeout_ms=(1 << sf) * 12_000 // bandwidth + 40)
            radio.sleep()
            if reply:
                return reply
        return None

    def _open(self, packet):
        """The application payload of a downlink meant for this device, or None."""
        if len(packet) < 12 or packet[0] not in (0x60, 0xA0) or packet[1:5] != self.dev_addr:
            return None
        # ponytail: the 16 bits on air as the whole downlink counter, so after 65535 downlinks the
        # signatures stop matching. Rejoin (delete the session file) long before that.
        fcnt = unpack("<H", packet[6:8])[0]
        if _signed(self.nwk_skey, self.dev_addr, fcnt, 1, packet[:-4]) != packet[-4:]:
            return None
        self._ack = packet[0] == 0xA0
        start = 8 + (packet[5] & 0x0F)  # past any network commands riding along in the header
        if start >= len(packet) - 4 or packet[start] == 0:
            return None  # only network commands, which this small stack ignores
        return _crypt(self.app_skey, self.dev_addr, fcnt, 1, packet[start + 1:-4])

    def _save(self):
        with open(self.session_file, "w") as f:
            json.dump({"dev_eui": hexlify(self.dev_eui).decode(),
                       "app_key": hexlify(self.app_key).decode(),
                       "dev_addr": hexlify(self.dev_addr).decode(),
                       "nwk_skey": hexlify(self.nwk_skey).decode(),
                       "app_skey": hexlify(self.app_skey).decode(),
                       "fcnt_up": self.fcnt_up, "rx1_delay": self.rx1_delay,
                       "rx1_offset": self.rx1_offset, "rx2_dr": self.rx2_dr}, f)
