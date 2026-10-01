from machine import I2C, Pin, SPI, unique_id
from time import ticks_diff, ticks_ms
import json
import select
import socket
import wifi
from meshtastic import Meshtastic
from sx127x import SX127x
from ssd1306 import SSD1306_I2C

# The node ID Meshtastic would use: the last four bytes of the MAC address.
node_id = int.from_bytes(unique_id()[-4:], "big")

# --- Configuration -----------------------------------------------------------------------------
# How other Meshtastic nodes and apps list this board. The short name is up to four characters.
long_name = "T3 Chat %04x" % (node_id & 0xFFFF)
short_name = "T3%02x" % (node_id & 0xFF)

# These three must match the Meshtastic devices you want to talk to. The defaults are what every
# Meshtastic device starts with: the LongFast preset on the default channel.
region = "EU_868"  # or US, ANZ, EU_433
preset = "LongFast"
channel = None  # None is the preset's own default channel

# dBm, 2 to 20. The EU_868 band Meshtastic uses allows more than most, so the maximum is fine there.
tx_power = 20

# The wifi network the board opens. None for an open network: anyone nearby can join and chat.
ssid = "Meshtastic-%04X" % (node_id & 0xFFFF)
password = None

# How often the board repeats its name to the mesh. Meshtastic's own default is three hours.
node_info_every_ms = 3 * 60 * 60 * 1000
# ----------------------------------------------------------------------------------------------

# LilyGO T3 LoRa32 V1.6.1: the radio, display and LED are wired on the board.
lora = SX127x(SPI(1, baudrate=5_000_000, sck=Pin(5), mosi=Pin(27), miso=Pin(19)),
              cs=Pin(18), reset=Pin(23), tx_power=tx_power)
display = SSD1306_I2C(128, 64, I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000))
led = Pin(25, Pin.OUT, value=0)

mesh = Meshtastic(lora, node_id, long_name, short_name, region=region, preset=preset,
                  channel=channel)
ap = wifi.access_point(ssid, password)
address = ap.ifconfig()[0]

messages = []  # the last 50, as the web page shows them
count = 0


def add(sender, text, mine, rssi=None, snr=None):
    global messages, count
    count += 1
    messages = messages[-49:] + [{"id": count, "from": sender, "text": text, "mine": mine,
                                  "rssi": rssi, "snr": snr}]
    show()


def show():
    """The wifi name and address to join, then the newest messages that fit."""
    display.fill(0)
    display.text(ssid, 0, 0, 1)
    display.text(address, 0, 10, 1)
    display.hline(0, 20, 128, 1)
    lines = []
    for message in messages[-4:]:
        text = ("> " if message["mine"] else message["from"][:6] + ": ") + message["text"]
        lines += [text[i:i + 16] for i in range(0, len(text), 16)]
    for row, line in enumerate(lines[-4:]):
        display.text(line, 0, 24 + row * 10, 1)
    display.show()


# --- The web page: everything in one file, served from the board --------------------------------
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b1116"><title>LoRa Chat</title>
<style>
:root{--bg:#0b1116;--panel:#131c23;--line:#22303a;--text:#e6edf1;--muted:#7d909c;
--accent:#67ea94;--mine:#1f6f47;--theirs:#1a252e}
@media (prefers-color-scheme:light){:root{--bg:#eef3f1;--panel:#fff;--line:#d5dfdb;--text:#10201a;
--muted:#62756c;--accent:#128a47;--mine:#c9f2d7;--theirs:#fff}}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--text);font:16px/1.4 system-ui,-apple-system,sans-serif;
display:flex;flex-direction:column}
header{display:flex;align-items:center;gap:.75rem;padding:.8rem 1rem;background:var(--panel);
border-bottom:1px solid var(--line);padding-top:max(.8rem,env(safe-area-inset-top))}
.logo{width:2.2rem;height:2.2rem;border-radius:50%;background:var(--accent);display:grid;
place-items:center;color:var(--bg);font-weight:800}
header h1{font-size:1rem;margin:0}
header small{color:var(--muted);display:flex;align-items:center;gap:.35rem}
.dot{width:.5rem;height:.5rem;border-radius:50%;background:var(--accent);
box-shadow:0 0 0 0 var(--accent);animation:pulse 2s infinite}
.dot.off{background:#d65;animation:none}
@keyframes pulse{70%{box-shadow:0 0 0 .4rem transparent}}
#nick{margin-left:auto;width:7rem;background:var(--bg);color:var(--text);border:1px solid var(--line);
border-radius:.6rem;padding:.4rem .6rem;font:inherit;font-size:.85rem}
main{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.5rem}
.empty{margin:auto;text-align:center;color:var(--muted);max-width:18rem}
.msg{max-width:80%;padding:.5rem .75rem;border-radius:1rem;background:var(--theirs);
border:1px solid var(--line);align-self:flex-start;animation:in .25s ease-out;overflow-wrap:anywhere}
.msg.mine{align-self:flex-end;background:var(--mine);border-color:transparent}
.msg b{display:block;font-size:.75rem;color:var(--accent)}
.msg i{display:block;font-size:.7rem;color:var(--muted);font-style:normal;margin-top:.15rem}
@keyframes in{from{opacity:0;transform:translateY(.4rem)}}
form{display:flex;gap:.5rem;padding:.75rem;background:var(--panel);border-top:1px solid var(--line);
padding-bottom:max(.75rem,env(safe-area-inset-bottom))}
#text{flex:1;min-width:0;background:var(--bg);color:var(--text);border:1px solid var(--line);
border-radius:1.4rem;padding:.7rem 1rem;font:inherit}
#text:focus,#nick:focus{outline:2px solid var(--accent);outline-offset:-1px}
button{border:0;border-radius:50%;width:2.9rem;height:2.9rem;background:var(--accent);color:var(--bg);
font-size:1.2rem;cursor:pointer}
button:disabled{opacity:.5}
#left{position:absolute;right:4.5rem;bottom:calc(env(safe-area-inset-bottom) + 1.3rem);
font-size:.7rem;color:var(--muted)}
</style></head><body>
<header><div class="logo">&#8859;</div><div><h1 id="node">LoRa Chat</h1>
<small><span class="dot" id="dot"></span><span id="state">Connecting</span></small></div>
<input id="nick" placeholder="Your name" maxlength="12" aria-label="Your name"></header>
<main id="list"><p class="empty" id="empty">Messages sent here go out over LoRa to every
Meshtastic node in range, and theirs appear here.</p></main>
<form id="form"><input id="text" autocomplete="off" placeholder="Message" aria-label="Message">
<span id="left"></span><button id="send" aria-label="Send">&#10148;</button></form>
<script>
const $=id=>document.getElementById(id);let last=0;
try{$("nick").value=localStorage.nick||""}catch(e){}
$("nick").onchange=()=>{try{localStorage.nick=$("nick").value}catch(e){}};
function full(){const n=$("nick").value.trim(),t=$("text").value.trim();return n&&t?n+": "+t:t}
function left(){const n=200-new TextEncoder().encode(full()).length;$("left").textContent=n<40?n:"";
$("send").disabled=n<0}
$("text").oninput=left;$("nick").oninput=left;
function add(m){$("empty")?.remove();const d=document.createElement("div");d.className="msg"+(m.mine?" mine":"");
if(!m.mine){const b=document.createElement("b");b.textContent=m.from;d.append(b)}
d.append(m.text);if(m.rssi!=null){const i=document.createElement("i");
i.textContent=m.rssi+" dBm \\u00b7 SNR "+m.snr.toFixed(1);d.append(i)}
const list=$("list"),end=list.scrollHeight-list.scrollTop-list.clientHeight<60;list.append(d);
if(end||m.mine)list.scrollTop=list.scrollHeight}
async function poll(){try{const r=await fetch("/messages?after="+last);const j=await r.json();
$("node").textContent=j.node;$("state").textContent="On air \\u00b7 "+j.radio;$("dot").className="dot";
for(const m of j.messages){add(m);last=m.id}}catch(e){$("state").textContent="Board out of reach";
$("dot").className="dot off"}setTimeout(poll,1500)}
$("form").onsubmit=async e=>{e.preventDefault();const t=full();if(!$("text").value.trim())return;
$("send").disabled=true;$("state").textContent="Sending over LoRa\\u2026";
try{const r=await fetch("/send",{method:"POST",body:t});if(r.ok){$("text").value=""}}catch(e){}
$("send").disabled=false;left();$("text").focus()};
poll();
</script></body></html>
""".encode()


def respond(connection, status, kind, body=b""):
    connection.sendall(("HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
                        "Cache-Control: no-store\r\nConnection: close\r\n\r\n"
                        % (status, kind, len(body))).encode())
    connection.sendall(body)


def serve(connection):
    request = b""
    while b"\r\n\r\n" not in request and len(request) < 4096:
        more = connection.recv(1024)
        if not more:
            return
        request += more
    head, _, body = request.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    method, path = lines[0].split(b" ")[:2]
    length = 0
    for line in lines[1:]:
        if line.lower().startswith(b"content-length:"):
            length = int(line[15:])
    while len(body) < min(length, 1024):
        more = connection.recv(length - len(body))
        if not more:
            break
        body += more

    if method == b"POST" and path == b"/send":
        try:
            text = body.decode().strip()
            mesh.send_text(text)  # blocks for the half second or so the radio is sending
        except (UnicodeError, ValueError):
            respond(connection, "400 Bad Request", "text/plain", b"1 to 200 bytes of text")
            return
        add(long_name, text, True)
        print("[me] %s" % text)
        respond(connection, "204 No Content", "text/plain")
    elif path.startswith(b"/messages"):
        after = int(path.partition(b"after=")[2] or 0)
        reply = {"node": long_name, "radio": "%s %.3f MHz" % (preset, lora.frequency / 1e6),
                 "messages": [m for m in messages if m["id"] > after]}
        respond(connection, "200 OK", "application/json", json.dumps(reply).encode())
    else:
        respond(connection, "200 OK", "text/html; charset=utf-8", PAGE)


web = socket.socket()
web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
web.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])
web.listen(5)
poller = select.poll()
poller.register(web, select.POLLIN)

print("Meshtastic node %s (!%08x) on %.3f MHz" % (long_name, node_id, lora.frequency / 1e6))
print("Join the wifi network %s and open http://%s" % (ssid, address))
show()
mesh.send_node_info()
node_info_at = ticks_ms()
led_on_at = None

while True:
    # Wait up to 50ms for a browser, then look at the radio: neither keeps the other waiting.
    for _ in poller.poll(50):
        connection, _ = web.accept()
        connection.settimeout(3)
        try:
            serve(connection)
        except (OSError, ValueError, IndexError):
            pass  # a browser that gave up halfway, or a request that made no sense
        finally:
            connection.close()

    received = mesh.recv()
    if received:
        sender, text = received
        add(mesh.name(sender), text, False, round(lora.rssi), lora.snr)
        print("[%s] %s" % (mesh.name(sender), text))
        led(1)
        led_on_at = ticks_ms()

    if led_on_at is not None and ticks_diff(ticks_ms(), led_on_at) > 150:
        led(0)
        led_on_at = None
    if ticks_diff(ticks_ms(), node_info_at) > node_info_every_ms:
        mesh.send_node_info()
        node_info_at = ticks_ms()
