# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-09

### Added
- Initial release: Self-hosted ICS proxy for Outlook Classic
- Flask-based HTTP proxy with `/proxy?url=<encoded-url>` endpoint
- Browser User-Agent spoofing to bypass Microsoft's ICS blocking
- In-memory caching with 5-minute TTL
- SSRF protection (blocks private IPs, localhost, reserved IPs)
- Gunicorn production WSGI server
- Docker multi-stage build (Alpine-based, non-root user)
- Docker Compose configuration with health checks and auto-restart
- Comprehensive README with setup & usage guide
- API reference documentation
- Security documentation
- Contributing guidelines
- MIT License

### Features
- `/proxy?url=<encoded-url>` - Proxy ICS URLs with browser UA
- `/healthz` - Health check endpoint
- `/` - Service info endpoint
- Request timeout (10s upstream, 5s health check)
- Response size limit (5 MB max)
- Structured logging to stdout
- Multi-worker Gunicorn (2 workers)

### Security
- SSRF protection for all private/reserved IP ranges
- Non-root container user
- Minimal Alpine base image
- No external API dependencies
- Local-only binding (127.0.0.1:8080) by default

### Documentation
- Quick start guide (3 commands)
- Outlook Classic integration steps
- Architecture decisions explained
- FAQ section
- Troubleshooting guide
