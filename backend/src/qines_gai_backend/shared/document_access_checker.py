from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.schemas.schema import T_Document

logger = get_logger(__name__)


@log_function_start_end
async def is_document_accesible(
    session: AsyncSession, document_id: str, user_id: str
) -> bool:
    """
    ドキュメントへのアクセス権をチェックする関数。

    Args:
        session: データベースセッションを指定します。データベースに対してクエリを実行するために使用されます。
        document_id: アクセス権限を確認したいドキュメントのIDを指定します。
        user_id: アクセスを試みているユーザーのIDを指定します。

    Returns:
        bool: ユーザーがドキュメントの所有者であるか「admin」である場合はTrueを返します。そうでない場合はFalseを返します。

    Raises:
        RuntimeError: エラー発生時はRuntimeErrorを発生させます。
    """
    try:
        select_query = select(T_Document.user_id).filter_by(document_id=document_id)
        result = await session.execute(select_query)
        document_owner = result.scalars().first()

        if document_owner == user_id or document_owner == "admin":
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise RuntimeError("An unexpected error occurred") from e
