def validate_byte_length(
    input_str: str, min_bytes: int, max_bytes: int, encoding: str = "utf-8"
) -> str:
    """入力された文字列に対して指定されたバイト数の範囲内であるかどうか検証する

    Args:
        input_str (str): 検証対象の文字列
        min_bytes (int): 許容できる最小バイト数
        max_bytes (int): 許容できる最大バイト数
        encoding (str, optional): 文字列をバイト列に変換するためのエンコーディング

    Returns:
        str: バイト数が範囲内の場合、入力文字列をそのまま返す

    Raises:
        ValueError: 範囲外のバイト数の場合、ValueErrorを発生させる
    """
    byte_length = len(input_str.encode(encoding))
    if byte_length < min_bytes:
        raise ValueError(f"Minimum {min_bytes} bytes")
    elif max_bytes < byte_length:
        raise ValueError(f"Maximum {max_bytes} bytes")
    return input_str
