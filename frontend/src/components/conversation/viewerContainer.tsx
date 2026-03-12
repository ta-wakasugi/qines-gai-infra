"use client";
import { THEME_COLORS } from "@/consts/color";
import { useArtifact } from "@/hooks/conversation/useArtifact";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useCollection } from "@/hooks/collection/useCollection";
import { useError } from "@/hooks/useError";
import { useLoading } from "@/hooks/useLoading";
import { useSnackbar } from "@/hooks/useSnackbar";
import { getCollectionDetail } from "@/actions/collection";
import { updateArtifact } from "@/actions/artifact";
import { addArtifact } from "@/actions/artifact";
import dynamic from "next/dynamic";
import { useMemo, useState, useEffect } from "react";
import { DownloadIcon } from "../icons/downloadIcon";
import MdPreview from "../markdown/mdPreview";
import { DownloadMenu } from "./downloadMenu";
import { useStreamingScroll } from "@/hooks/useStreamingScroll";
const PdfViewer = dynamic(() => import("@/components/pdf/pdfViewer"), {
  ssr: false,
});

/**
 * ビューワーコンテナのカスタムフック
 * PDFとMarkdownのプレビュー表示に関する状態と操作を管理
 * @returns {object} ビューワーの状態と操作メソッド
 */
const useViewerContainer = () => {
  const { commonButtonDisabled, setCommonButtonDisabled } = useButtonDisabled();
  const { base64Pdf, resetPdf } = usePdf();
  const { collection, setCollection } = useCollection();
  const { showError, errorTemplate } = useError();
  const { showLoading, hideLoading, setLoadingText } = useLoading();
  const { showSnackbar } = useSnackbar();
  const { textContent, textTitle, resetText } = usePlainText();
  const {
    artifact,
    resetArtifact,
    setArtifact,
    getArtifactByIdAndVersion,
    getMaxVersionById,
    addArtifactToDocumentMapping,
    getDocumentIdByArtifactId,
  } = useArtifact();
  const { scrollContainerRef } = useStreamingScroll(artifact ? artifact.content : "");
  const [artifactVersion, setArtifactVersion] = useState(
    artifact ? artifact.version : 1
  );
  // artifactが変更されたときにartifactVersionを同期
  useEffect(() => {
    if (artifact && artifact.version) {
      setArtifactVersion(artifact.version);
    }
  }, [artifact]);
  const [isVisibleDownloadMenu, setIsVisibleDownloadMenu] = useState<boolean>(false);
  const artifactMaxVersion = getMaxVersionById(artifact?.id || "");

  // アーティファクトがコレクション内に存在するかの判定
  const isArtifactInCollection = useMemo(() => {
    if (!artifact?.id || !collection?.documents) return false;

    // アーティファクトIDに対応するドキュメントIDを取得
    const documentId = getDocumentIdByArtifactId(artifact.id);

    // ドキュメントIDがある場合は、それがコレクション内に存在するかチェック
    // ドキュメントIDがない場合は、アーティファクトIDで直接チェック（後方互換性）
    const targetId = documentId || artifact.id;
    const exists = collection.documents.some((doc) => doc.id === targetId);

    return exists;
  }, [
    artifact?.id,
    collection?.documents,
    collection?.updated_at,
    getDocumentIdByArtifactId,
  ]);

  // ボタン表示制御
  const showOverwriteButton = isArtifactInCollection;
  const showNewSaveButton = !isArtifactInCollection;

  const versionOptions = [];
  if (artifact) {
    for (let version = 1; version <= artifactMaxVersion; version++) {
      versionOptions.push(version);
    }
  }
  const changeVersion = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setArtifactVersion(Number(e.target.value));
    if (!artifact) return;
    const changeArtifact = getArtifactByIdAndVersion(
      artifact.id,
      Number(e.target.value)
    );
    if (changeArtifact) {
      setArtifact(changeArtifact);
    }
  };

  // 新規追加処理
  const handleNewSave = async () => {
    if (!artifact || !collection?.public_collection_id) return;

    setCommonButtonDisabled(true);
    showLoading();
    setLoadingText("新規追加中...");

    try {
      // バックエンドAPI呼び出し - 成果物を更新
      const result = await addArtifact({
        public_collection_id: collection.public_collection_id,
        artifact_id: artifact.id,
        version: artifact.version,
      });
      // 更新成功時のみ処理を続行
      if (result.success) {
        // アーティファクトIDとドキュメントIDのマッピングを追加
        if (result.document_id) {
          addArtifactToDocumentMapping(artifact.id, result.document_id);
        }

        // フロントエンド状態更新
        const updatedCollection = await getCollectionDetail(
          collection.public_collection_id
        );
        if (updatedCollection) {
          setCollection(updatedCollection);
        }
        // ユーザーフィードバック
        showSnackbar("追加しました", true, 3000);
      } else {
        // 新規追加失敗時はAPIからのメッセージを表示
        showError(result.message || errorTemplate.api);
      }
    } catch (error) {
      console.error("新規追加エラー:", error);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hideLoading();
    }
  };

  // 上書き保存処理
  const handleOverwriteSave = async () => {
    if (!artifact || !collection?.public_collection_id) return;

    setCommonButtonDisabled(true);
    showLoading();
    setLoadingText("更新中...");

    try {
      // バックエンドAPI呼び出し - 成果物を更新
      const result = await updateArtifact({
        public_collection_id: collection.public_collection_id,
        artifact_id: artifact.id,
        version: artifact.version,
      });
      // 更新成功時のみ処理を続行
      if (result.success) {
        // フロントエンド状態更新
        const updatedCollection = await getCollectionDetail(
          collection.public_collection_id
        );
        if (updatedCollection) {
          setCollection(updatedCollection);
        }
        // ユーザーフィードバック
        showSnackbar("更新しました", true, 3000);
      } else {
        // 更新失敗時はAPIからのメッセージを表示
        showError(result.message || errorTemplate.api);
      }
    } catch (error) {
      console.error("更新エラー:", error);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hideLoading();
    }
  };

  // 高さ計算関数
  const calculateViewerHeight = (isStacked = false) => {
    // baseHeader.tsx:65,89行目 h-[40px] + ビューワータイトルバー py-1(8px*2) + 余白(8px) = 88px
    const baseOffset = 88;
    // アーティファクト存在時の追加オフセット: ビューワータイトルバー py-1(8px*2) + コンテンツ余白等(24px) = 40px
    const stackOffset = isStacked ? 40 : 0;
    return `calc(100vh - ${baseOffset + stackOffset}px)`;
  };

  // アーティファクト存在判定
  const existArtifact = Boolean(artifact);

  // PDFビューアーはPDFデータが存在し、テキストデータが存在しない場合のみ
  const PdfViewerContainer = useMemo(() => {
    if (base64Pdf && !textContent) {
      return <PdfViewer width="100%" height={calculateViewerHeight(existArtifact)} />;
    }
    return null;
  }, [base64Pdf, textContent, existArtifact]);

  const PlainTextViewerContainer = useMemo(() => {
    if (!textContent || !textTitle) return null;

    return (
      <div className="relative border rounded-xl bg-white">
        <div className="flex border justify-between items-center bg-white py-1 px-2 rounded-xl rounded-b-none">
          <div className="ml-2">{textTitle}</div>
          <button className="text-action-blue text-2xl mr-2" onClick={resetText}>
            ×
          </button>
        </div>
        <div
          className="overflow-auto p-4 bg-white"
          style={{ height: calculateViewerHeight(existArtifact), width: "100%" }}
        >
          <MdPreview source={textContent} />
        </div>
      </div>
    );
  }, [textContent, textTitle, resetText, existArtifact]);

  const resetFile = () => {
    resetPdf();
    resetText();
  };

  // ファイルタイプの判定
  const isTextMode = Boolean(textContent && !base64Pdf);
  const isPdfMode = Boolean(base64Pdf && !textContent);

  return {
    commonButtonDisabled,
    scrollContainerRef,
    base64Pdf,
    textContent,
    resetPdf: resetFile,
    isVisibleDownloadMenu,
    setIsVisibleDownloadMenu,
    artifact,
    resetArtifact,
    versionOptions,
    PdfViewerContainer,
    PlainTextViewerContainer,
    artifactVersion,
    changeVersion,
    showOverwriteButton,
    showNewSaveButton,
    handleNewSave,
    handleOverwriteSave,
    isTextMode,
    isPdfMode,
    calculateViewerHeight,
  };
};

type HooksType = ReturnType<typeof useViewerContainer>;

/**
 * ビューワーコンテナのビューコンポーネント
 * @param {object} props - プロパティ
 * @param {HooksType} props.hooks - useViewerContainerフックの戻り値
 */
const ViewerContainerView = ({ hooks }: { hooks: HooksType }) => {
  const existFile = Boolean(hooks.base64Pdf || hooks.textContent);
  const buttonDisabled = hooks.commonButtonDisabled || existFile;
  const buttonColor = buttonDisabled
    ? THEME_COLORS.buttonDisabled
    : THEME_COLORS.button;
  const buttonText = buttonDisabled ? "text-light-gray" : "text-action-blue";
  const titleBg = buttonDisabled ? "bg-gray-100" : "bg-white";
  const titleTextFocus = buttonDisabled ? "hover:underline cursor-pointer" : "";
  const existArtifact = Boolean(hooks.artifact);
  const fileViewerHeight = existArtifact ? "top-[40px]" : "";

  return (
    <>
      <div className="relative h-full">
        {hooks.artifact && (
          <div
            className="absolute top-0 w-full"
            style={{ height: hooks.calculateViewerHeight() }}
          >
            <DownloadMenu
              isVisible={hooks.isVisibleDownloadMenu}
              onClose={() => hooks.setIsVisibleDownloadMenu(false)}
              artifact={hooks.artifact}
            />
            <div
              className={`flex border border-b-0 justify-between items-center py-1 px-2 rounded-xl rounded-b-none w-full ${titleBg}`}
            >
              <div className="flex ml-2 flex-1 overflow-hidden items-center">
                <p
                  className={`text-action-blue text-ellipsis overflow-hidden whitespace-nowrap ${titleTextFocus}`}
                  onClick={hooks.resetPdf}
                >
                  {hooks.artifact.title}
                </p>
                <select
                  className={`text-sm ml-3 mr-3 cursor-pointer ${titleBg}`}
                  disabled={buttonDisabled}
                  value={hooks.artifactVersion}
                  onChange={hooks.changeVersion}
                >
                  {hooks.versionOptions.toReversed().map((version, index) => (
                    <option key={index} value={version}>
                      Version: {version}
                    </option>
                  ))}
                </select>
                {/* 更新ボタン - アーティファクトがコレクション内に存在する場合のみ表示 */}
                {hooks.showOverwriteButton && (
                  <button
                    className={`px-3 py-1 text-sm text-white rounded-md mr-3 ${buttonDisabled ? "bg-light-gray" : "bg-action-blue"}`}
                    disabled={buttonDisabled}
                    onClick={hooks.handleOverwriteSave}
                  >
                    更新
                  </button>
                )}
                {/* 新規追加ボタン - アーティファクトがコレクション内に存在しない場合のみ表示 */}
                {hooks.showNewSaveButton && (
                  <button
                    className={`px-3 py-1 text-sm text-white rounded-md mr-3 ${buttonDisabled ? "bg-light-gray" : "bg-action-blue"}`}
                    disabled={buttonDisabled}
                    onClick={hooks.handleNewSave}
                  >
                    新規追加
                  </button>
                )}
              </div>
              <div className="flex items-center">
                <button
                  className="text-action-blue text-2xl mr-5"
                  disabled={buttonDisabled}
                  onClick={() => hooks.setIsVisibleDownloadMenu(true)}
                >
                  <DownloadIcon color={buttonColor} />
                </button>
                <button
                  className={`text-2xl mr-2 ${buttonText}`}
                  disabled={buttonDisabled}
                  onClick={hooks.resetArtifact}
                >
                  ×
                </button>
              </div>
            </div>
            {/* コンテンツ表示 */}
            <div className="p-2 mx-2 flex-1 flex flex-col h-full overflow-hidden">
              <div
                className="flex-1 overflow-y-auto px-[20px]"
                ref={hooks.scrollContainerRef}
              >
                <MdPreview
                  source={hooks.artifact.content}
                  className="w-full !bg-transparent !text-inherit"
                />
              </div>
            </div>
          </div>
        )}
        {hooks.isTextMode && (
          <div className={`absolute w-full ${fileViewerHeight}`}>
            {hooks.PlainTextViewerContainer}
          </div>
        )}
        {hooks.isPdfMode && (
          <div className={`absolute w-full ${fileViewerHeight}`}>
            {hooks.PdfViewerContainer}
          </div>
        )}
      </div>
    </>
  );
};

/**
 * ビューワーコンテナのメインコンポーネント
 * PDFとMarkdownプレビューの表示を制御
 */
export const ViewerContainer = () => {
  const hooks = useViewerContainer();
  return <ViewerContainerView hooks={hooks} />;
};
