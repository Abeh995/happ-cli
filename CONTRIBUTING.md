# Contributing to Happ CLI

Thank you for your interest in contributing to **Happ CLI**! Whether you are reporting a bug, proposing a new feature, improving documentation, or submitting code changes, your contributions are welcome.

---

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free experience for everyone. Please be respectful and constructive in all discussions, issues, and code reviews.

---

## Getting Started

1. **Fork the Repository** on GitHub: [github.com/Abeh995/happ-cli](https://github.com/Abeh995/happ-cli).
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/happ-cli.git
   cd happ-cli
   ```
3. **Set up upstream remote**:
   ```bash
   git remote add upstream https://github.com/Abeh995/happ-cli.git
   ```

---

## Development & Building

### Go Engine (Core)
The core CLI engine is written in Go (1.24+).

```bash
# Run unit and integration tests
go test ./...

# Vet and lint
go vet ./...

# Build local binary
go build -o bin/happ ./cmd/happ
```

### Windows Suite (TUI Dashboard & Daemons)
The Windows headless suite is located in `windows/`:
- `windows/happ_core.py`: Python 3.8+ headless orchestrator, TUI dashboard, and multi-daemon supervisor.
- `windows/happ.cmd`: Command-line launcher entry point.
- `windows/install.ps1`: Automated PowerShell one-click installer.

Syntax check for Windows script:
```powershell
python -m py_compile windows/happ_core.py
```

---

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat(scope): add new capability`
- `fix(scope): resolve issue or regression`
- `docs(scope): update documentation`
- `refactor(scope): internal code restructuring`
- `test(scope): add or improve test coverage`
- `chore(scope): build, CI, or dependency update`

---

## Pull Request Lifecycle

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-new-feature
   ```
2. Implement your changes with clear, focused commits.
3. Verify all tests pass:
   ```bash
   go test ./...
   python -m py_compile windows/happ_core.py
   ```
4. Push your branch to your fork:
   ```bash
   git push origin feat/my-new-feature
   ```
5. Open a Pull Request against `Abeh995/happ-cli` on GitHub using the provided PR template.

---

## License

By contributing to Happ CLI, you agree that your contributions will be licensed under the project's [GNU General Public License v3.0 (GPL-3.0)](LICENSE).
