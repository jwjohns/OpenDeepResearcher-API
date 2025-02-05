# Contributing to OpenDeepResearcher

First off, thank you for considering contributing to OpenDeepResearcher! It's people like you that make OpenDeepResearcher such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

1. **Use a clear and descriptive title**
2. **Describe the exact steps to reproduce the problem**
3. **Provide specific examples to demonstrate the steps**
4. **Describe the behavior you observed after following the steps**
5. **Explain which behavior you expected to see instead and why**
6. **Include screenshots and animated GIFs if possible**
7. **Include your environment details**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

1. **Use a clear and descriptive title**
2. **Provide a step-by-step description of the suggested enhancement**
3. **Provide specific examples to demonstrate the steps**
4. **Describe the current behavior and explain the behavior you expected to see instead**
5. **Explain why this enhancement would be useful**

### Pull Requests

1. **Fork the repo and create your branch from `main`**
2. **If you've added code that should be tested, add tests**
3. **If you've changed APIs, update the documentation**
4. **Ensure the test suite passes**
5. **Make sure your code lints**
6. **Issue that pull request!**

## Development Process

1. **Setting up your development environment**
```bash
# Clone your fork
git clone https://github.com/<your-username>/OpenDeepResearcher.git

# Add upstream remote
git remote add upstream https://github.com/original/OpenDeepResearcher.git

# Create virtual environment
python -m venv venv-odr-310
source venv-odr-310/bin/activate  # On Unix/macOS
# or
.\venv-odr-310\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

2. **Making Changes**
- Create a topic branch from where you want to base your work
- Make commits of logical and atomic units
- Follow our coding style
- Add or update tests as needed
- Run tests locally before pushing

3. **Commit Messages**
We follow conventional commits. Format your commit messages as:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that don't affect the code's meaning
- refactor: Code change that neither fixes a bug nor adds a feature
- perf: Code change that improves performance
- test: Adding missing tests
- chore: Changes to the build process or auxiliary tools

Example:
```
feat(research): add support for PDF output format

- Implement PDF generation using WeasyPrint
- Add PDF styling templates
- Update documentation with PDF examples

Closes #123
```

## Style Guide

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions focused and small
- Use meaningful variable names

### Documentation Style Guide

- Use Markdown for documentation
- Include code examples where appropriate
- Keep line length to 80-100 characters
- Use proper heading hierarchy
- Include links to referenced issues/PRs

## Testing

- Write unit tests for new features
- Update existing tests when modifying features
- Ensure all tests pass before submitting PR
- Include integration tests where appropriate

## Project Structure

```
OpenDeepResearcher/
├── app/                    # Main application code
├── tests/                  # Test files
├── docs/                   # Documentation
├── research_outputs/       # Generated research files
└── scripts/               # Utility scripts
```

## Getting Help

- Join our Discord server
- Check the documentation
- Open an issue
- Contact the maintainers

## Recognition

Contributors will be recognized in:
- The project's README
- Our documentation
- Release notes

## Additional Notes

### Issue and Pull Request Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation only changes
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## License

By contributing, you agree that your contributions will be licensed under the MIT License. 