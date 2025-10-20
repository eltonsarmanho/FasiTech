from src.utils.validators import is_valid_cpf


def test_is_valid_cpf_basic() -> None:
    assert is_valid_cpf("123.456.789-09") is True
    assert is_valid_cpf("00000000000") is True
    assert is_valid_cpf("123") is False
