#!/usr/bin/env python3
"""Probe ILOCKIT Cloud endpoints to see which respond for your account/devices."""
import asyncio
import json
import os
import secrets
from aiohttp import ClientSession, BasicAuth

BASE = os.getenv("ILOCKIT_BASE", "https://tracking.ilockit.bike")
USER = os.getenv("ILOCKIT_USER")
PASS = os.getenv("ILOCKIT_PASS")
# Set ILOCKIT_RUN_RISKY=1 to include disruptive commands (lock/unlock, reboot, alarm, theft mode).
RUN_RISKY = os.getenv("ILOCKIT_RUN_RISKY") == "1"


def ensure_creds():
    if not USER or not PASS:
        raise SystemExit("Set ILOCKIT_USER and ILOCKIT_PASS env vars")


async def req(session, method, path, **kwargs):
    url = f"{BASE}{path}"
    try:
        async with session.request(method, url, **kwargs) as r:
            text = await r.text()
            return r.status, text
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def build_commands():
    """Return command payloads to probe; risky ones gated by env."""
    cmds = {
        "lockInfo": {"id": 5},
        "request_position": {"id": 15},
        "signalSound": {"id": 4},
        "arm_alarm": {"id": 6},
        "disarm_alarm": {"id": 7},
        "alarm_off": {"id": 12},
        "restart_gps": {"id": 11},
        "theft_on": {"id": 10, "attributes": {"theft": "true"}},
        "theft_off": {"id": 10, "attributes": {"theft": "false"}},
        "config_alarmmode": {"id": 9, "attributes": {"alarmmode": 34}},
        "config_sound": {"id": 9, "attributes": {"sound": 5}},
        "config_proximity": {"id": 9, "attributes": {"lockConfig": {"proximityUnlock": True}}},
    }
    risky = {
        "locking_open": {"id": 3, "attributes": {"direction": "open"}},
        "locking_close": {"id": 3, "attributes": {"direction": "close"}},
        "reboot_device": {"id": 8},
    }
    if RUN_RISKY:
        cmds.update(risky)
    return cmds


async def probe_commands(session, device_id):
    results = {}
    for name, payload in build_commands().items():
        body = {**payload, "deviceId": device_id}
        # add seed for locking if not provided
        if body.get("id") == 3 and "lockingSeed" not in (body.get("attributes") or {}):
            body.setdefault("attributes", {})["lockingSeed"] = secrets.token_hex(16)
        st, txt = await req(
            session,
            "POST",
            "/api/commands/send",
            json=body,
            headers={"accept": "application/json", "content-type": "application/json"},
        )
        entry = {"status": st, "body": txt[:200]}
        # fetch event if available
        try:
            evt = json.loads(txt).get("eventId")
            if evt:
                st2, txt2 = await req(session, "GET", "/api/events", params={"eventId": evt})
                entry["event"] = {"status": st2, "body": txt2[:200]}
        except Exception:
            pass
        results[name] = entry
    return results


async def main():
    ensure_creds()
    auth = BasicAuth(USER, PASS)
    async with ClientSession(auth=auth, headers={"accept": "application/json"}) as s:
        results: dict = {}

        # Devices
        status, text = await req(s, "GET", "/api/devices")
        devices = json.loads(text) if status == 200 else []
        results["devices"] = {"status": status, "count": len(devices)}

        # Positions
        status_pos, text_pos = await req(s, "GET", "/api/positions")
        results["positions"] = {"status": status_pos, "sample": text_pos[:200]}

        per_device = []
        for d in devices:
            did = d.get("id")
            name = d.get("name")
            dev_result = {"deviceId": did, "name": name}

            # Commands
            dev_result["commands"] = await probe_commands(s, did)

            # firmware info by name
            st_fw, txt_fw = await req(s, "GET", "/api/devices/firmware", params={"name": name})
            dev_result["firmware"] = {"status": st_fw, "body": txt_fw[:200]}

            per_device.append(dev_result)

        # Events list (groupId required; try 0 or adjust)
        st_ev, txt_ev = await req(s, "GET", "/api/reports/events", params={"groupId": 0, "limit": 10})
        results["events_list"] = {"status": st_ev, "body": txt_ev[:200]}

        results["per_device"] = per_device
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
