#!/usr/bin/env python3
"""
outlook-ics-proxy: Self-hosted ICS proxy for Outlook Classic.
Forwards ICS URLs with a browser User-Agent to work around Microsoft's blocking.
"""

import os
import logging
import json
import urllib.parse
import ipaddress
from time import time
from functools import wraps

import requests
from flask import Flask, request, Response, jsonify

# ============================================================================
# Configuration
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
BROWSER_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)
UPSTREAM_TIMEOUT = 10  # seconds
CACHE_TTL = 300  # 5 minutes
MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB

# In-memory cache: {url_hash: (timestamp, content, content_type)}
_cache = {}

# ============================================================================
# SSRF Protection
# ============================================================================

def is_private_ip(hostname):
    """
    Check if hostname resolves to a private/reserved IP.
    Blocks: localhost, 127.x.x.x, 10.x.x.x, 172.16-31.x.x, 192.168.x.x,
            169.254.x.x (link-local), 0.0.0.0, 255.255.255.255, etc.
    """
    try:
        # Try to parse as IP directly
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_loopback or
            ip.is_private or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_unspecified or
            ip == ipaddress.ip_address('255.255.255.255')
        )
    except ValueError:
        pass

    # Resolve hostname
    try:
        import socket
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_loopback or
            ip.is_private or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_unspecified
        )
    except Exception:
        # If resolution fails, assume it's safe (might be CDN, etc.)
        return False


def validate_url(url_str):
    """
    Validate and sanitize incoming URL.
    Returns (is_valid, error_message, parsed_url).
    """
    if not url_str:
        return False, "Missing 'url' parameter", None

    if len(url_str) > 2048:
        return False, "URL too long (max 2048 chars)", None

    try:
        parsed = urllib.parse.urlparse(url_str)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}", None

    # Scheme check
    if parsed.scheme not in ('http', 'https'):
        return False, "Only http/https schemes allowed", None

    # Hostname check
    if not parsed.hostname:
        return False, "Missing hostname in URL", None

    # SSRF check
    if is_private_ip(parsed.hostname):
        return False, f"Private/reserved IP blocked: {parsed.hostname}", None

    return True, None, parsed


# ============================================================================
# Caching
# ============================================================================

def cache_key(url_str):
    """Generate a simple cache key from URL."""
    return hash(url_str) & 0x7fffffff  # Positive int


def get_cached(url_str):
    """Get cached response if valid and not expired."""
    key = cache_key(url_str)
    if key in _cache:
        timestamp, content, content_type = _cache[key]
        age = time() - timestamp
        if age < CACHE_TTL:
            logger.info(f"Cache hit for {url_str} (age: {age:.1f}s)")
            return content, content_type
        else:
            del _cache[key]
            logger.info(f"Cache expired for {url_str} (age: {age:.1f}s)")
    return None, None


def set_cache(url_str, content, content_type):
    """Store response in cache."""
    key = cache_key(url_str)
    _cache[key] = (time(), content, content_type)
    logger.info(f"Cached {url_str} ({len(content)} bytes)")


# ============================================================================
# Proxying
# ============================================================================

def fetch_ics(url_str):
    """
    Fetch ICS from upstream URL with browser User-Agent.
    Returns (status_code, content, content_type, error_message).
    """
    headers = {
        'User-Agent': BROWSER_USER_AGENT,
        'Accept': 'text/calendar, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
    }

    try:
        logger.info(f"Fetching {url_str}")
        resp = requests.get(
            url_str,
            headers=headers,
            timeout=UPSTREAM_TIMEOUT,
            allow_redirects=True,
            stream=True
        )

        # Check response size
        content_length = resp.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            return None, None, None, f"Response too large: {content_length} bytes"

        # Read response
        content = resp.content
        if len(content) > MAX_RESPONSE_SIZE:
            return None, None, None, "Response too large after reading"

        # Determine content type
        content_type = resp.headers.get('Content-Type', 'text/calendar')
        # Normalize to text/calendar if it looks like ICS
        if 'calendar' in content_type or 'ics' in content_type:
            content_type = 'text/calendar; charset=utf-8'
        elif not content_type.startswith('text/'):
            content_type = 'text/calendar; charset=utf-8'

        logger.info(
            f"Fetched {url_str}: {resp.status_code} "
            f"({len(content)} bytes, {content_type})"
        )

        return resp.status_code, content, content_type, None

    except requests.Timeout:
        return None, None, None, f"Upstream timeout (>{UPSTREAM_TIMEOUT}s)"
    except requests.ConnectionError as e:
        return None, None, None, f"Connection error: {str(e)}"
    except requests.RequestException as e:
        return None, None, None, f"Request failed: {str(e)}"
    except Exception as e:
        return None, None, None, f"Unexpected error: {str(e)}"


# ============================================================================
# Flask Routes
# ============================================================================

@app.route('/proxy', methods=['GET'])
def proxy():
    """
    Proxy endpoint for ICS URLs.
    Usage: GET /proxy?url=https%3A%2F%2Fcalendar.google.com%2Fcalendar%2Fics%2F...
    """
    url_param = request.args.get('url', '').strip()

    # Validate URL
    is_valid, error_msg, parsed_url = validate_url(url_param)
    if not is_valid:
        logger.warning(f"Invalid URL: {error_msg}")
        return (
            jsonify({
                'error': error_msg,
                'status': 'invalid_url'
            }),
            400,
            {'Content-Type': 'application/json'}
        )

    # Reconstruct full URL
    url_str = urllib.parse.urlunparse(parsed_url)

    # Try cache
    cached_content, cached_type = get_cached(url_str)
    if cached_content is not None:
        return Response(cached_content, content_type=cached_type)

    # Fetch from upstream
    status_code, content, content_type, error = fetch_ics(url_str)

    if error:
        logger.error(f"Fetch failed: {error}")
        return (
            jsonify({
                'error': error,
                'status': 'fetch_failed',
                'url': url_str
            }),
            502,
            {'Content-Type': 'application/json'}
        )

    # Cache on success
    if status_code and 200 <= status_code < 300:
        set_cache(url_str, content, content_type)

    return Response(content, status=status_code, content_type=content_type)


@app.route('/healthz', methods=['GET'])
def healthz():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with basic info."""
    return jsonify({
        'service': 'outlook-ics-proxy',
        'version': '1.0',
        'endpoints': {
            '/proxy?url=<ics-url>': 'Fetch and proxy ICS calendar',
            '/healthz': 'Health check'
        }
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found', 'status': 'not_found'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed', 'status': 'method_not_allowed'}), 405


# ============================================================================
# Entry point
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting outlook-ics-proxy on port {port}")
    app.run(host='127.0.0.1', port=port, debug=debug, threaded=True)
