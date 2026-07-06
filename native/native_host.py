#!/usr/bin/env python3

import json
import os
import struct
import subprocess
import sys

APP = "/opt/vgca/vgca_xeonline"

REQUEST = "/tmp/vgca_request.json"


def read_msg():
    raw = sys.stdin.buffer.read(4)

    if len(raw) == 0:
        sys.exit(0)

    length = struct.unpack("<I", raw)[0]

    data = sys.stdin.buffer.read(length)

    return json.loads(data.decode())


def send_msg(obj):

    data = json.dumps(obj).encode()

    sys.stdout.buffer.write(struct.pack("<I", len(data)))

    sys.stdout.buffer.write(data)

    sys.stdout.flush()


while True:

    req = read_msg()

    # Lưu request để App đọc
    with open(REQUEST, "w", encoding="utf8") as f:

        json.dump(req, f)

    # Mở App
    subprocess.Popen([APP])

    send_msg({

        "success": True

    })