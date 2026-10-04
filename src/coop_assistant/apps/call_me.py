"""Callback mode: the laptop asks Twilio to ring a phone and run the local AI call flow.

Usage: python -m coop_assistant.apps.call_me --url <public_url> --to <phone> --from <twilio_number>
Credentials come from TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN (process or Windows user environment).
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _env(name):
    value = os.environ.get(name)
    if not value and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value = winreg.QueryValueEx(key, name)[0]
    return value


def call(public_url, to, from_):
    sid, token = _env("TWILIO_ACCOUNT_SID"), _env("TWILIO_AUTH_TOKEN")
    auth = "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()
    data = urllib.parse.urlencode({"To": to, "From": from_, "Url": f"{public_url.rstrip('/')}/voice"}).encode()
    req = urllib.request.Request(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json", data,
                                 headers={"Authorization": auth})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
        print(f"Calling {result['to']} from {result['from']} (status: {result['status']})")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        raise SystemExit(f"Twilio refused the call: {err.get('code')} {err.get('message')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", required=True, help="public tunnel URL of the running call server")
    parser.add_argument("--to", required=True, help="phone to ring, E.164 format")
    parser.add_argument("--from", dest="from_", default=os.environ.get("TWILIO_PHONE_NUMBER"),
                        help="your Twilio number (default: TWILIO_PHONE_NUMBER)")
    args = parser.parse_args()
    if not args.from_:
        parser.error("--from or TWILIO_PHONE_NUMBER is required")
    call(args.url, args.to, args.from_)
