"""
Local OAuth helper for TikTok for Developers.

Recommended production-review flow:
1) Put TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and TIKTOK_REDIRECT_URI in .env.
2) Run: python src_tiktok_oauth.py auth-url --open
3) Authorize the app with the TikTok account that should receive drafts.
4) Copy the code from the HTTPS callback page.
5) Run: python src_tiktok_oauth.py exchange --code <code>
"""

import argparse
import json
import os
import secrets
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv, set_key
from flask import Flask, redirect, request

load_dotenv()

APP_ROOT = Path(__file__).resolve().parent
ENV_PATH = APP_ROOT / ".env"

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
REDIRECT_HOST = "http://localhost"
REDIRECT_PORT = 8000
LOCAL_REDIRECT_URI = f"{REDIRECT_HOST}:{REDIRECT_PORT}/callback"
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", LOCAL_REDIRECT_URI)

AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

SCOPES = [
    scope.strip()
    for scope in os.getenv("TIKTOK_SCOPES", "video.upload,user.info.basic").split(",")
    if scope.strip()
]
EXPECTED_STATE = secrets.token_urlsafe(24)

app = Flask(__name__)


def build_authorize_url(client_key, redirect_uri, scopes, state=EXPECTED_STATE):
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": ",".join(scopes),
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return AUTHORIZE_URL + "?" + urlencode(params)


def exchange_code_for_token(client_key, client_secret, code, redirect_uri):
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
            data=data,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        response = getattr(exc, "response", None)
        return {"error": str(exc), "raw": response.text if response is not None else None}


def write_tokens_to_env(tokens):
    if not ENV_PATH.exists():
        ENV_PATH.touch()

    set_key(str(ENV_PATH), "TIKTOK_CLIENT_KEY", CLIENT_KEY)
    set_key(str(ENV_PATH), "TIKTOK_CLIENT_SECRET", CLIENT_SECRET)
    for token_key, env_key in [
        ("access_token", "TIKTOK_ACCESS_TOKEN"),
        ("refresh_token", "TIKTOK_REFRESH_TOKEN"),
        ("expires_in", "TIKTOK_EXPIRES_IN"),
        ("refresh_expires_in", "TIKTOK_REFRESH_EXPIRES_IN"),
        ("open_id", "TIKTOK_OPEN_ID"),
        ("scope", "TIKTOK_GRANTED_SCOPES"),
    ]:
        if token_key in tokens:
            set_key(str(ENV_PATH), env_key, str(tokens.get(token_key, "")))

    set_key(str(ENV_PATH), "TIKTOK_TOKEN_RAW", json.dumps(tokens))


def token_data_from_result(result):
    if isinstance(result, dict) and result.get("data"):
        return result["data"]
    if isinstance(result, dict) and ("access_token" in result or "refresh_token" in result):
        return result
    raise RuntimeError("Token exchange failed: " + json.dumps(result, ensure_ascii=False))


def exchange_and_store(code, redirect_uri=REDIRECT_URI):
    result = exchange_code_for_token(CLIENT_KEY, CLIENT_SECRET, code, redirect_uri)
    token_data = token_data_from_result(result)
    write_tokens_to_env(token_data)
    return {
        "status": "tokens_written",
        "env_path": str(ENV_PATH),
        "redirect_uri": redirect_uri,
        "granted_scopes": token_data.get("scope"),
        "expires_in": token_data.get("expires_in"),
        "refresh_expires_in": token_data.get("refresh_expires_in"),
    }


@app.route("/")
def index():
    return "<p>TikTok OAuth helper. Go to /start to begin local authorization.</p>"


@app.route("/start")
def start():
    if not CLIENT_KEY or not CLIENT_SECRET:
        return (
            "TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET missing in .env. "
            "Please set them and restart this script."
        ), HTTPStatus.BAD_REQUEST
    return redirect(build_authorize_url(CLIENT_KEY, LOCAL_REDIRECT_URI, SCOPES))


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"Authorization failed: {error}", HTTPStatus.BAD_REQUEST

    if request.args.get("state") != EXPECTED_STATE:
        return "Invalid OAuth state.", HTTPStatus.BAD_REQUEST

    code = request.args.get("code")
    if not code:
        return "No code provided in callback.", HTTPStatus.BAD_REQUEST

    try:
        exchange_and_store(code, LOCAL_REDIRECT_URI)
    except Exception as exc:
        return f"Token exchange failed: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR

    return (
        "Authorization successful. Tokens written to .env. You can close this page and return to the terminal."
        "<br><br><b>Important:</b> do not share your tokens publicly."
    ), HTTPStatus.OK


def open_browser_start():
    url = f"http://localhost:{REDIRECT_PORT}/start"
    print("Opening browser to:", url)
    webbrowser.open(url, new=2, autoraise=True)


def serve_local():
    print("TikTok OAuth helper - starting local server on port", REDIRECT_PORT)
    print("Redirect URI must match the one configured in your TikTok app:", LOCAL_REDIRECT_URI)
    print("Scopes:", ",".join(SCOPES))
    open_browser_start()
    app.run(host="127.0.0.1", port=REDIRECT_PORT, debug=False)


def print_auth_url(open_in_browser=False, redirect_uri=REDIRECT_URI):
    if not CLIENT_KEY:
        raise RuntimeError("TIKTOK_CLIENT_KEY is missing in .env")
    url = build_authorize_url(CLIENT_KEY, redirect_uri, SCOPES)
    print(url)
    if open_in_browser:
        webbrowser.open(url, new=2, autoraise=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TikTok OAuth helper.")
    sub = parser.add_subparsers(dest="command")

    auth = sub.add_parser("auth-url")
    auth.add_argument("--open", action="store_true")
    auth.add_argument("--redirect-uri", default=REDIRECT_URI)

    exchange = sub.add_parser("exchange")
    exchange.add_argument("--code", required=True)
    exchange.add_argument("--redirect-uri", default=REDIRECT_URI)

    sub.add_parser("serve")

    args = parser.parse_args(argv)
    if args.command == "auth-url":
        print_auth_url(args.open, args.redirect_uri)
    elif args.command == "exchange":
        result = exchange_and_store(args.code, args.redirect_uri)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        serve_local()


if __name__ == "__main__":
    main()
