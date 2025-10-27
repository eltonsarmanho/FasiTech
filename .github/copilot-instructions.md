# Copilot Instructions for FasiTech

## Project Overview
FasiTech is a modern web forms platform built with Streamlit (frontend) and FastAPI (backend), running on EC2. It integrates with Google Drive, Google Sheets, and email notifications. The platform centralizes multiple institutional forms for academic workflows.

## Architecture & Key Components
- **src/app/**: Streamlit app entry (`main.py`) and individual form pages (`pages/`).
- **src/services/**: Business logic for file uploads, Google integrations, and email.
- **src/models/**: Pydantic schemas for data validation.
- **src/utils/**: Utilities for validation, encoding, PDF generation, and environment loading.
- **api/**: Optional FastAPI backend for webhooks and dependencies.
- **config/**: Environment-specific configuration files (`dev/`, `prod/`).
- **credentials/**: Google credentials, separated by environment.
- **docker/**: Containerization files.
- **scripts/**: Automation and deployment scripts.
- **tests/**: Test suite for services and utilities.

## Developer Workflows
- **App Startup**: Use `./scripts/start.sh` (recommended) to set up environment variables and launch Streamlit. Manual alternatives require setting `PYTHONPATH` and activating the virtual environment.
- **Testing**: Place tests in `tests/`. Use `pytest` for running tests. Service logic is tested in `tests/test_services/`, utilities in `tests/test_utils/`.
- **Imports**: All form pages add the project root to `sys.path` for absolute imports (e.g., `from src.services.form_service import ...`). Always run from the project root to avoid import errors.

## Patterns & Conventions
- **Form Handling**: Each form is a separate Python file in `src/app/pages/`, using service functions for processing and Google integrations.
- **Google Integration**: Credentials are loaded from `credentials/{env}/` and config from `config/{env}/config.yaml`. Services handle Drive/Sheets logic.
- **Email Notifications**: Triggered via service layer after successful submissions.
- **Environment Separation**: Use `dev` and `prod` folders for config and credentials. Never mix credentials between environments.
- **Containerization**: Use `docker/Dockerfile` for building images. Scripts automate deployment.

## Troubleshooting
- **ModuleNotFoundError**: Ensure you run from the project root and set `PYTHONPATH` correctly. Prefer the startup script.
- **Unresolved Imports in VSCode**: Add the project root to VSCode's Python path settings.

## Examples
- Form page import:
  ```python
  from src.services.form_service import process_acc_submission
  from src.models.schemas import AccSubmission
  ```
- Service usage:
  ```python
  from src.services.google_drive import upload_file
  from src.services.google_sheets import register_submission
  ```

## References
- See `README.md` and `src/README.md` for more details on structure and workflows.
- Key files: `src/app/main.py`, `src/app/pages/`, `src/services/`, `scripts/start.sh`, `config/`, `credentials/`, `tests/`

---
_Review and update these instructions as the project evolves. Feedback welcome for unclear or missing sections._
