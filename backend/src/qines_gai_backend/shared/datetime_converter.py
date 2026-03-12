import pytz


def convert_datetime_utc_to_jst(utc_dt):
    """UTCのdatetimeオブジェクトをJSTの文字列に変換します。

    Args:
        utc_dt: UTCのdatetimeオブジェクト

    Returns:
        datetime: JSTのdatetimeオブジェクト
    """
    jst_dt = utc_dt.astimezone(pytz.timezone("Asia/Tokyo"))
    return jst_dt
