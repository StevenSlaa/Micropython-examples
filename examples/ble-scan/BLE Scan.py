# Listing the Bluetooth Low Energy devices around you.
#
# BLE devices that want to be found advertise: they shout a short packet every so often, and
# anything listening hears it. No connection and no pairing is involved, which is why this
# works on a fitness band you have never met.

import asyncio
import aioble

# --- Configuration ---------------------------------------------------------------------------
# how long to listen for, in milliseconds
duration_ms = 5000

# active=True asks each device for its name, which costs an extra exchange per device. Without
# it most results have no name at all, because names do not fit in the first packet.
active = True

# seconds between scans
interval = 5
# ----------------------------------------------------------------------------------------------


def strength(rssi):
    """RSSI is in dBm and always negative. Closer to zero is closer to you."""
    if rssi > -60:
        return "very close"
    if rssi > -75:
        return "nearby"
    if rssi > -90:
        return "in range"
    return "far"


async def scan_once():
    found = []

    # interval and window together decide how much of the time the radio is listening. Equal
    # values mean continuously, which finds the most and uses the most power.
    async with aioble.scan(duration_ms, interval_us=30000, window_us=30000, active=active) as scanner:
        async for result in scanner:
            found.append(result)

    # Strongest first: the closest things are usually the ones you are looking for.
    found.sort(key=lambda result: result.rssi, reverse=True)

    print("Found: %d devices" % len(found))
    for result in found:
        # A device that advertises no name is normal. Most things do not.
        name = result.name() or "(no name)"
        # Services it advertises, when it says: 0x180f is battery, 0x180d heart rate.
        services = ", ".join(str(uuid) for uuid in result.services()) or "none advertised"
        print(
            "%-22s Signal: %4d dBm  %-10s Connectable: %-5s Services: %s"
            % (name, result.rssi, strength(result.rssi), result.connectable, services)
        )


async def main():
    while True:
        print("Scanning for %d ms..." % duration_ms)
        await scan_once()
        print()
        await asyncio.sleep(interval)


asyncio.run(main())
