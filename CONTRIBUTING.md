# Contributing to outlook-ics-proxy

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

- Be respectful and constructive
- Focus on improving the project
- Keep discussions on-topic

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Git

### Local Development

1. **Fork & clone the repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/outlook-ics-proxy.git
   cd outlook-ics-proxy
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Build locally**
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Test your changes**
   ```bash
   docker compose logs -f outlook-ics-proxy
   # Test in browser or with curl
   ```

5. **Commit with a clear message**
   ```bash
   git commit -m "Add feature description"
   ```

6. **Push & create a Pull Request**
   ```bash
   git push origin feature/my-feature
   ```

## What to Contribute

### Bug Fixes

If you find a bug:
1. Open an issue with a clear title
2. Include steps to reproduce
3. Attach logs (`docker compose logs`)
4. Submit a PR with the fix

### Features

For new features:
1. Open an issue first for discussion
2. Keep it minimal (align with project philosophy)
3. Add/update tests if applicable
4. Update README if user-facing
5. Submit a PR

### Documentation

- Typos, unclear instructions → submit a fix
- Better examples → welcome
- Translations → consider the maintenance burden

## Code Style

- **Python**: Keep it simple, readable, ~300 LOC for the main app
- **Naming**: Clear, descriptive, English
- **Comments**: Explain *why*, not *what*
- **Security**: Always consider SSRF, timeouts, size limits

## Testing

### Manual Testing

```bash
# Health check
curl http://127.0.0.1:8080/healthz

# Proxy with a test URL (must be public, non-private IP)
curl 'http://127.0.0.1:8080/proxy?url=https%3A%2F%2Fexample.com%2Fcalendar.ics'

# Check logs
docker compose logs -f outlook-ics-proxy
```

### Before Submitting

- [ ] Tested locally with `docker compose`
- [ ] Logs show no errors
- [ ] SSRF protection still blocks private IPs
- [ ] Health check passes
- [ ] README updated if needed

## Pull Request Process

1. **Title**: Clear, concise (e.g., "Fix SSRF check for IPv6 localhost")
2. **Description**: Explain what & why
3. **Link to issue**: If fixing a bug/feature request
4. **One feature per PR**: Keep changes focused

## Commit Message Format

```
Verb: Brief description

Longer explanation if needed.
```

**Examples:**
- `Fix: SSRF check for IPv6 addresses`
- `Add: Prometheus metrics endpoint`
- `Refactor: Cache key generation`
- `Docs: Update README with CalDAV example`

## Project Philosophy

This project prioritizes:
- **Simplicity** over features
- **Security** over convenience (SSRF, timeouts)
- **Maintainability** over cleverness
- **Minimal dependencies** (Flask, requests, Gunicorn only)

Before adding dependencies or complexity, consider:
- Is it essential?
- Can it be simpler?
- Will it be maintained long-term?

## Ideas for Contribution

Looking for ideas?

- [ ] **Tests**: Add pytest for edge cases
- [ ] **Docs**: Clarify setup for different OS
- [ ] **Logging**: Better structured logs
- [ ] **CI/CD**: GitHub Actions for tests
- [ ] **Cache**: Optional Redis/SQLite backend
- [ ] **Metrics**: Prometheus endpoint
- [ ] **Security**: Rate limiting, request validation

## Questions?

- Open an issue for questions
- Check existing issues/PRs first
- Join discussions respectfully

---

**Happy contributing!** 🚀
