class BaseAppError(Exception):
    """
    アプリケーションのベース例外クラス
    すべてのカスタム例外の基底クラスとなります
    """

    def __init__(self, message: str = "アプリケーションエラーが発生しました"):
        self.message = message
        super().__init__(self.message)


class ConversationNotFoundError(BaseAppError):
    def __init__(self, message: str = "Conversation not found"):
        super().__init__(message)


class NotAuthorizedConversation(BaseAppError):
    def __init__(self, message: str = "Not authorized to access this conversation"):
        super().__init__(message)


class CollectionValidationError(BaseAppError):
    """コレクション関連のバリデーションエラー"""

    def __init__(self, message: str = "Collection validation failed"):
        super().__init__(message)


class CollectionNotFoundError(BaseAppError):
    """コレクションが見つからない場合のエラー"""

    def __init__(self, message: str = "Collection not found"):
        super().__init__(message)


class NotAuthorizedCollectionError(BaseAppError):
    """コレクションへのアクセス権限がない場合のエラー"""

    def __init__(self, message: str = "Not authorized to access this collection"):
        super().__init__(message)


class DocumentValidationError(BaseAppError):
    """ドキュメント関連のバリデーションエラー"""

    def __init__(self, message: str = "Document validation failed"):
        super().__init__(message)


class DocumentNotFoundError(BaseAppError):
    """ドキュメントが見つからない場合のエラー"""

    def __init__(self, message: str = "Document not found"):
        super().__init__(message)


class DocumentNotAuthorizedError(BaseAppError):
    """ドキュメントへのアクセス権限がない場合のエラー"""

    def __init__(self, message: str = "Not authorized to access this document"):
        super().__init__(message)


class DocumentUpdateError(BaseAppError):
    """ドキュメントの更新に失敗した場合のエラー"""

    def __init__(self, message: str = "Not authorized to access this document"):
        super().__init__(message)


class DocumentUpdateValidationError(BaseAppError):
    """ドキュメント更新時のバリデーションエラー"""

    def __init__(self, message: str = "Not authorized to access this document"):
        super().__init__(message)


class AIServiceError(BaseAppError):
    """AI関連のサービスエラー"""

    def __init__(self, message: str = "AI service error occurred"):
        super().__init__(message)


class CollectionCreationError(BaseAppError):
    """コレクション作成エラー"""

    def __init__(self, message: str = "Failed to create collection"):
        super().__init__(message)


class ChatProcessingError(BaseAppError):
    """チャット処理エラー"""

    def __init__(self, message: str = "Failed to process chat request"):
        super().__init__(message)


class TitleGenerationError(BaseAppError):
    """タイトル生成エラー"""

    def __init__(self, message: str = "Failed to generate title"):
        super().__init__(message)


class ArtifactNotFoundError(BaseAppError):
    """成果物が見つからない場合のエラー"""

    def __init__(self, message: str = "Artifact not found"):
        super().__init__(message)
