# Contributing

Thanks for your interest in contributing! Here's how you can help.

## Quick Ways to Help

- **Star the repo** - Helps others find this project
- **Report bugs** - Open an issue with details
- **Suggest features** - We're open to ideas
- **Share** - Tell people who work with medical data

## Code Contributions

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/medical-pii-removal.git
cd medical-pii-removal
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Style

- Use Black for formatting: `black src/ api/ ui/`
- Use type hints where possible
- Keep functions focused and small

### Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Ideas for Contributions

### High Priority
- [ ] Add more languages (Spanish, French, German)
- [ ] Create Jupyter notebook examples
- [ ] Add batch file processing CLI
- [ ] Improve documentation

### Medium Priority
- [ ] VS Code extension
- [ ] Fine-tuning guide for specific specialties
- [ ] Performance benchmarking suite
- [ ] Docker Compose for local development

### Lower Priority
- [ ] Web UI improvements
- [ ] Additional replacement strategies
- [ ] Integration tests
- [ ] CI/CD pipeline

## Questions?

Open an issue or start a discussion. We're friendly!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
