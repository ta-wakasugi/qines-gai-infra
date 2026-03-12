import pytest
from qines_gai_backend.shared.byte_length_validater import validate_byte_length

# テストケースを定義
# (input_str, min_bytes, max_bytes, expected_exception)
test_cases = [
    # 正常系
    ("abc", 1, 3, None),  # 境界値: 最小・最大
    ("あいう", 1, 9, None),  # マルチバイト文字
    ("a", 1, 1, None),  # 境界値: 最小・最大が同じ
    ("", 0, 10, None),  # 空文字列
    # 異常系
    ("ab", 3, 5, ValueError),  # 最小バイト数未満
    ("abcd", 1, 3, ValueError),  # 最大バイト数超過
    ("あいうえお", 1, 14, ValueError),  # マルチバイト文字で最大バイト数超過
    ("あ", 4, 10, ValueError),  # マルチバイト文字で最小バイト数未満
]


@pytest.mark.parametrize(
    "input_str, min_bytes, max_bytes, expected_exception", test_cases
)
def test_validate_byte_length(input_str, min_bytes, max_bytes, expected_exception):
    """
    validate_byte_length関数のテスト
    """
    if expected_exception:
        with pytest.raises(expected_exception):
            validate_byte_length(input_str, min_bytes, max_bytes)
    else:
        result = validate_byte_length(input_str, min_bytes, max_bytes)
        assert result == input_str


def test_validate_byte_length_encoding():
    """
    エンコーディングが異なる場合のテスト
    """
    input_str = "あ"
    # Shift_JISの場合、"あ"は2バイト
    result = validate_byte_length(input_str, 1, 2, encoding="shift_jis")
    assert result == input_str

    with pytest.raises(ValueError):
        validate_byte_length(input_str, 3, 5, encoding="shift_jis")
