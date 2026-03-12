import pytest

from qines_gai_backend.config.dependencies.data_connection import get_connection_manager
from qines_gai_backend.schemas.schema import T_Document
from qines_gai_backend.shared.document_access_checker import is_document_accesible


@pytest.fixture(scope="function")
async def initialize_connections():
    connection_manager = get_connection_manager()
    await connection_manager.connect_all()
    try:
        yield
    finally:
        await connection_manager.disconnect_all()


@pytest.fixture(scope="function", autouse=True)
async def session(initialize_connections):
    connection_manager = get_connection_manager()
    async with connection_manager.get_connection("postgresql").get_session() as session:
        trans = await session.begin()  # トランザクションを開始
        try:
            yield session
        finally:
            await trans.rollback()  # トランザクションをロールバックしてデータを元に戻す


# 01:チェックOKケース（ユーザ一致）
async def test_is_document_accesible_01(session):
    new_item = T_Document(
        document_id="11111111-1111-1111-1111-111111111111",
        file_name="test.pdf",
        file_path="path/test.pdf",
        file_type="application/pdf",
        file_size=100,
        user_id="test_user",
        metadata_info={},
    )
    session.add(new_item)
    await session.flush()

    result = await is_document_accesible(
        session, "11111111-1111-1111-1111-111111111111", "test_user"
    )
    assert result


# 02:チェックOKケース（マスターデータ）
async def test_is_document_accesible_02(session):
    new_item = T_Document(
        document_id="11111111-1111-1111-1111-111111111111",
        file_name="test.pdf",
        file_path="path/test.pdf",
        file_type="application/pdf",
        file_size=100,
        user_id="admin",  # マスターデータ
        metadata_info={},
    )
    session.add(new_item)
    await session.flush()

    # データベースの内容を確認
    result = await is_document_accesible(
        session, "11111111-1111-1111-1111-111111111111", "test_user"
    )
    assert result


# 03:チェックNGケース（ユーザ不一致）
async def test_is_document_accesible_03(session):
    new_item = T_Document(
        document_id="11111111-1111-1111-1111-111111111111",
        file_name="test.pdf",
        file_path="path/test.pdf",
        file_type="application/pdf",
        file_size=100,
        user_id="test_user",
        metadata_info={},
    )
    session.add(new_item)
    await session.flush()

    result = await is_document_accesible(
        session, "11111111-1111-1111-1111-111111111111", "ng_user"
    )
    assert not result


# 04:チェックNGケース（ドキュメントが存在しない）
async def test_is_document_accesible_04(session):
    new_item = T_Document(
        document_id="11111111-1111-1111-1111-111111111111",
        file_name="test.pdf",
        file_path="path/test.pdf",
        file_type="application/pdf",
        file_size=100,
        user_id="test_user",
        metadata_info={},
    )
    session.add(new_item)
    await session.flush()

    result = await is_document_accesible(
        session, "22222222-2222-2222-2222-222222222222", "test_user"
    )
    assert not result


# 05:エラーケース（Exception）
async def test_is_document_accesible_05(session, mocker):
    new_item = T_Document(
        document_id="11111111-1111-1111-1111-111111111111",
        file_name="test.pdf",
        file_path="path/test.pdf",
        file_type="application/pdf",
        file_size=100,
        user_id="test_user",
        metadata_info={},
    )
    session.add(new_item)
    await session.flush()

    mocker.patch(
        "qines_gai_backend.schemas.schema.T_Document",
        side_effect=Exception("An error occurred"),
    )

    session_mock = mocker.Mock()
    with pytest.raises(RuntimeError) as excinfo:
        await is_document_accesible(
            session_mock, "11111111-1111-1111-1111-111111111111", "test_user"
        )

    assert "An unexpected error occurred" in str(excinfo.value)
