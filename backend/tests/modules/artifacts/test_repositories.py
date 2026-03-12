import pytest
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.schemas.schema import T_Artifact, T_Collection


class TestArtifactRepository:
    """ArtifactRepositoryのテストクラス"""

    class TestGetArtifactByIdAndVersion:
        """get_artifact_by_id_and_versionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_and_version_success(self, test_data_creator):
            """成果物IDとバージョンで成果物を正常に取得できることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )

                # 成果物を作成
                artifact_version_id = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Test Artifact", version=1
                )
                await test_data_creator.session.commit()

                # 成果物のartifact_idを取得
                select_stmt = select(T_Artifact).filter_by(
                    artifact_version_id=artifact_version_id
                )
                result = await test_data_creator.session.execute(select_stmt)
                artifact = result.scalars().first()

                # Repository を使って成果物を取得
                repository = ArtifactRepository(test_data_creator.session)
                result_artifact = await repository.get_artifact_by_id_and_version(
                    artifact.artifact_id, 1
                )

                # Assert
                assert result_artifact is not None
                assert result_artifact.artifact_id == artifact.artifact_id
                assert result_artifact.version == 1
                assert result_artifact.title == "Test Artifact"

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_and_version_not_found(
            self, test_data_creator
        ):
            """存在しない成果物IDとバージョンで成果物が見つからない場合のテスト"""
            # Repository を使って存在しない成果物を取得
            repository = ArtifactRepository(test_data_creator.session)
            nonexistent_id = uuid.uuid4()
            result = await repository.get_artifact_by_id_and_version(nonexistent_id, 1)

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_and_version_wrong_version(
            self, test_data_creator
        ):
            """正しいIDだが存在しないバージョンで成果物が見つからない場合のテスト"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )

                # バージョン1の成果物を作成
                artifact_version_id = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Test Artifact", version=1
                )
                await test_data_creator.session.commit()

                # 成果物のartifact_idを取得
                select_stmt = select(T_Artifact).filter_by(
                    artifact_version_id=artifact_version_id
                )
                result = await test_data_creator.session.execute(select_stmt)
                artifact = result.scalars().first()

                # Repository を使ってバージョン2の成果物を取得（存在しない）
                repository = ArtifactRepository(test_data_creator.session)
                result_artifact = await repository.get_artifact_by_id_and_version(
                    artifact.artifact_id, 2
                )

                # Assert
                assert result_artifact is None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_and_version_multiple_versions(
            self, test_data_creator
        ):
            """同じ成果物IDの異なるバージョンを正しく取得できることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )

                # 同じartifact_idで異なるバージョンの成果物を作成
                artifact_version_id_1 = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Test Artifact v1", version=1
                )
                await test_data_creator.session.commit()

                # 成果物のartifact_idを取得
                select_stmt = select(T_Artifact).filter_by(
                    artifact_version_id=artifact_version_id_1
                )
                result = await test_data_creator.session.execute(select_stmt)
                artifact_v1 = result.scalars().first()

                # artifact_idを変数に保存（セッション外でアクセスするため）
                saved_artifact_id = artifact_v1.artifact_id

                # バージョン2を手動で作成
                artifact_v2 = T_Artifact(
                    artifact_id=saved_artifact_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    title="Test Artifact v2",
                    content="Updated content",
                    version=2,
                )
                test_data_creator.session.add(artifact_v2)
                await test_data_creator.session.commit()

                # Repository を使って各バージョンを取得
                repository = ArtifactRepository(test_data_creator.session)
                result_v1 = await repository.get_artifact_by_id_and_version(
                    saved_artifact_id, 1
                )
                result_v2 = await repository.get_artifact_by_id_and_version(
                    saved_artifact_id, 2
                )

                # Assert
                assert result_v1 is not None
                assert result_v2 is not None
                assert result_v1.version == 1
                assert result_v2.version == 2
                assert result_v1.title == "Test Artifact v1"
                assert result_v2.title == "Test Artifact v2"
                assert result_v1.artifact_id == result_v2.artifact_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCommit:
        """commitメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_commit_success(self, test_data_creator):
            """トランザクションのコミットが正常に動作することを確認する"""
            try:
                # テストデータを作成（コミットせずに）
                collection_id = await test_data_creator.create_test_collection()

                # Repository を使ってコミット
                repository = ArtifactRepository(test_data_creator.session)
                await repository.commit()

                # コミット後にデータが存在することを確認
                select_stmt = select(T_Collection).filter_by(
                    collection_id=collection_id
                )
                result = await test_data_creator.session.execute(select_stmt)
                collection = result.scalars().first()

                # Assert
                assert collection is not None
                assert collection.collection_id == collection_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestRollback:
        """rollbackメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_rollback_success(self, test_data_creator):
            """トランザクションのロールバックが正常に動作することを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )
                artifact_version_id = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Test Artifact", version=1
                )

                # コミット前にロールバック
                repository = ArtifactRepository(test_data_creator.session)
                await repository.rollback()

                # ロールバック後にデータが存在しないことを確認
                select_stmt = select(T_Artifact).filter_by(
                    artifact_version_id=artifact_version_id
                )
                result = await test_data_creator.session.execute(select_stmt)
                artifact = result.scalars().first()

                # Assert
                assert artifact is None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise
