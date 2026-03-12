import asyncio
import inspect
import logging
import os
from functools import wraps


def get_logger(name: str):
    """
    与えられた名前でロガーインスタンスを取得する関数。
    ログレベルは環境変数 LOG_LEVEL で設定する。（デフォルトはINFO）

    引数:
        name (str): ロガーの名前。通常はモジュール名。

    戻り値:
        logging.Logger: 設定済みのロガーインスタンス。
    """
    logger = logging.getLogger(name)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def log_function_start_end(func):
    """
    関数呼び出しの開始と終了をログに記録するデコレーター。
    ログレベルがDEBUGに設定されている場合は、関数に渡された引数と戻り値も
    ログに記録する。

    引数:
        func (Callable): デコレーターでラップする関数。

    戻り値:
        Callable: ラップされた関数。
    """
    if inspect.isasyncgenfunction(func):

        @wraps(func)
        async def async_gen_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.info(f"Starting {func.__name__} function...")

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Args: {args}, Kwargs: {kwargs}")

            async for item in func(*args, **kwargs):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Return value: {item}")
                yield item

            logger.info(f"Finished {func.__name__} function.")

        return async_gen_wrapper

    elif asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.info(f"Starting {func.__name__} function...")

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Args: {args}, Kwargs: {kwargs}")

            result = await func(*args, **kwargs)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Return value: {result}")

            logger.info(f"Finished {func.__name__} function.")

            return result

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.info(f"Starting {func.__name__} function...")

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Args: {args}, Kwargs: {kwargs}")

            result = func(*args, **kwargs)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Return value: {result}")

            logger.info(f"Finished {func.__name__} function.")

            return result

        return sync_wrapper
