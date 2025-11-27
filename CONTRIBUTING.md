# Contributing to LLM Search Scout

Thank you for your interest in contributing to LLM Search Scout! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Docker version, etc.)

### Suggesting Features

Feature suggestions are welcome! Please open an issue describing:
- The use case for the feature
- How it would work
- Any potential implementation details

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/josephvolmer/llm-search-scout.git
   cd llm-search-scout
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

4. **Test your changes**
   ```bash
   docker compose up --build
   # Run manual tests or automated tests
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Describe what your PR does
   - Reference any related issues
   - Include screenshots if relevant

## Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### Local Development

1. Clone and setup:
   ```bash
   git clone https://github.com/josephvolmer/llm-search-scout.git
   cd llm-search-scout
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. Start services:
   ```bash
   docker compose up --build
   ```

3. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Code Style

- **Python**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for function arguments and return values
- **Docstrings**: Add docstrings for all public functions and classes
- **Comments**: Comment complex logic

### Testing

Currently, the project uses manual testing. Automated tests are welcome contributions!

Manual testing checklist:
- [ ] Health endpoint works
- [ ] Standard search returns results
- [ ] Streaming search works
- [ ] Rate limiting functions correctly
- [ ] API key authentication works
- [ ] AI features work (if OpenAI key configured)

### Areas for Contribution

We especially welcome contributions in these areas:

**High Priority:**
- Automated test suite (pytest, integration tests)
- Additional citation formats (IEEE, Vancouver, etc.)
- Better content type detection algorithms
- Enhanced credibility scoring
- Performance optimizations

**Medium Priority:**
- Redis-backed rate limiting for multi-instance deployments
- Result caching layer
- Additional AI providers (Anthropic Claude, local models)
- Image search support
- Fact extraction and verification

**Documentation:**
- More integration examples
- Video tutorials
- Deployment guides (Kubernetes, cloud platforms)
- Translation to other languages

## Questions?

Feel free to open an issue for any questions about contributing!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
