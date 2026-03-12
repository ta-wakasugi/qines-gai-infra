"use client";
import { downloadArtifact } from "@/actions/artifact";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import { ArtifactType } from "@/models/conversation";
import { BasePopupMenu } from "../popupMenu/basePopupMenu";
import { getNowDateTimeString } from "../utils/datetime";
import { useSnackbar } from "@/hooks/useSnackbar";
import Snackbar from "../utils/snackbar";

const LOADING_TEXT = "ダウンロード中...";

type Props = {
  isVisible: boolean;
  onClose: () => void;
  artifact: ArtifactType;
};

/**
 * ダウンロードメニューのカスタムフック
 * @param {Props} props - メニューの表示状態と成果物情報
 */
const useDownloadMenu = (props: Props) => {
  const { showError, errorTemplate } = useError();
  const { setCommonButtonDisabled, commonButtonDisabled } = useButtonDisabled();
  const { showSnackbar, hiddenSnackbar } = useSnackbar();

  interface DownloadAction {
    (blob: Blob, filename: string): void;
  }

  /**
   * ファイルをダウンロードする共通処理
   * @param {Blob} blob - ダウンロードするファイルデータ
   * @param {string} filename - ダウンロードするファイル名
   */
  const downloadAction: DownloadAction = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.download = filename;
    a.href = url;
    a.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Markdown形式でダウンロードする処理
   * @param {React.FormEvent<HTMLFormElement>} event - イベントオブジェクト
   */
  const handleDownloadMarkdown = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      setCommonButtonDisabled(true);
      showSnackbar(LOADING_TEXT, false);
      const downloadFileName = `qines_${getNowDateTimeString()}.md`;
      props.onClose();
      const blob = new Blob([props.artifact.content], { type: "text/markdown" });
      downloadAction(blob, downloadFileName);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hiddenSnackbar();
    }
  };

  /**
   * PowerPoint形式でダウンロードする処理
   * @param {React.FormEvent<HTMLFormElement>} event - イベントオブジェクト
   */
  const handleDownloadPowerPoint = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const downloadFileName = `qines_${getNowDateTimeString()}.pptx`;
    props.onClose();
    try {
      setCommonButtonDisabled(true);
      showSnackbar(LOADING_TEXT, false);
      const downloadData = await downloadArtifact({
        artifact_id: props.artifact.id,
        version: props.artifact.version,
        format: "pptx",
      });
      const decodedContent = Buffer.from(downloadData.content, "base64");
      const blob = new Blob([decodedContent], {
        type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      });
      downloadAction(blob, downloadFileName);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hiddenSnackbar();
    }
  };

  /**
   * PDF形式でダウンロードする処理
   * @param {React.FormEvent<HTMLFormElement>} event - イベントオブジェクト
   */
  const handleDownloadPdf = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const downloadFileName = `qines_${getNowDateTimeString()}.pdf`;
    props.onClose();
    try {
      showSnackbar(LOADING_TEXT, false);
      setCommonButtonDisabled(true);
      const response = await fetch("/api/artifact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mdContent: props.artifact.content }),
      });
      const blob = await response.blob();
      downloadAction(blob, downloadFileName);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hiddenSnackbar();
    }
  };

  return {
    commonButtonDisabled,
    handleDownloadMarkdown,
    handleDownloadPowerPoint,
    handleDownloadPdf,
  };
};

/**
 * ダウンロードメニューのビューコンポーネント
 * @param {object} param - プロパティとフック
 * @param {Props} param.props - メニューの表示状態と成果物情報
 * @param {ReturnType<typeof useDownloadMenu>} param.hooks - useDownloadMenuフックの戻り値
 */
const DownloadMenuView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: ReturnType<typeof useDownloadMenu>;
}) => {
  return (
    <>
      <Snackbar />
      <BasePopupMenu
        className="top-8 right-12"
        isVisible={props.isVisible}
        onClose={props.onClose}
      >
        <div className="flex-col items-start flex w-32">
          <form
            onSubmit={hooks.handleDownloadMarkdown}
            className="pl-2 py-1 w-full hover:bg-gray-100 cursor-pointer"
          >
            <button className="w-full text-left" disabled={hooks.commonButtonDisabled}>
              Markdown
            </button>
          </form>
          <form
            onSubmit={hooks.handleDownloadPowerPoint}
            className="border-y pl-2 py-1 border-gray-300 w-full hover:bg-gray-100 cursor-pointer"
          >
            <button className="w-full text-left" disabled={hooks.commonButtonDisabled}>
              PowerPoint
            </button>
          </form>
          <form
            onSubmit={hooks.handleDownloadPdf}
            className="pl-2 py-1 w-full hover:bg-gray-100 cursor-pointer"
          >
            <button className="w-full text-left" disabled={hooks.commonButtonDisabled}>
              PDF
            </button>
          </form>
        </div>
      </BasePopupMenu>
    </>
  );
};

/**
 * ダウンロードメニューのメインコンポーネント
 * @param {Props} props - メニューの表示状態と成果物情報
 */
export const DownloadMenu = (props: Props) => {
  const hooks = useDownloadMenu(props);
  return <DownloadMenuView props={props} hooks={hooks} />;
};
