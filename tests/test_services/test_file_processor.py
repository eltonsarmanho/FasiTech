from src.services.file_processor import sanitize_submission


def test_sanitize_submission_removes_formatting() -> None:
    data = {"cpf": "123.456.789-09", "name": "Test", "registration": "  2023001  "}
    sanitized = sanitize_submission(data)
    assert sanitized["cpf"] == "12345678909"
    assert sanitized["registration"] == "2023001"
