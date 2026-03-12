import { updateCollection } from "@/actions/collection";
import { uploadDocument } from "@/actions/document";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { useCollection } from "@/hooks/collection/useCollection";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useDragDropUpload } from "@/hooks/useDragDropUpload";
import { useError } from "@/hooks/useError";
import { useEffect, useRef } from "react";
import { DropzoneInputProps } from "react-dropzone";
import { PlusBoxIcon } from "../icons/plusBoxIcon";
import { useSnackbar } from "@/hooks/useSnackbar";
import Snackbar from "../utils/snackbar";

/**
 * ファイルアップローダーのカスタムフック
 * @param isUploadOnly - アップロードのみを行うかどうか
 * @returns アップローダーの状態と操作関数を含むオブジェクト
 */
const useFileUploader = (isUploadOnly: boolean) => {
  const { collection, setCollection, getDocumentIds } = useCollection();
  const { addCollectionDocument } = useSearchCollectionDocuments();
  const { commonButtonDisabled, setCommonButtonDisabled, buttonColor } =
    useButtonDisabled();
  const { showSnackbar, hiddenSnackbar } = useSnackbar();
  const { showError, errorTemplate } = useError();
  const { uploadFile, setUploadFile } = useDragDropUpload();
  const formRef = useRef<HTMLFormElement>(null);

  /**
   * ファイルアップロードを処理する関数
   */
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await showSnackbar("アップロード中...", false);
    setCommonButtonDisabled(true);
    try {
      if (!uploadFile) return;
      // ServerActionsでは日本語ファイル名が文字化けするため別途受け取る
      const fileName = uploadFile.name;
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("file_name", fileName); // ServerActionsでは日本語ファイル名が文字化けするため別途送信
      const document = await uploadDocument(formData);
      if (isUploadOnly || !collection) {
        addCollectionDocument(document);
        return;
      }
      const documentIds = getDocumentIds();
      documentIds.push(document.id);
      const resultCollection = await updateCollection(collection.public_collection_id, {
        name: collection.name,
        document_ids: documentIds,
      });
      setCollection(resultCollection);
    } catch (error) {
      console.error(error);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      setUploadFile(null);
      hiddenSnackbar();
    }
  };
  useEffect(() => {
    if (formRef.current) {
      formRef.current.requestSubmit();
    }
  }, [uploadFile]);
  return { formRef, handleSubmit, commonButtonDisabled, buttonColor };
};

type Props = {
  open: () => void;
  getInputProps: <T extends DropzoneInputProps>(props?: T) => T;
  buttonLabel: string;
  isUploadOnly: boolean;
};

type hooks = ReturnType<typeof useFileUploader>;

/**
 * ファイルアップローダーのビューコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns ファイルアップローダーのJSX要素
 */
const FileUploaderView = ({ props, hooks }: { props: Props; hooks: hooks }) => {
  const textColor = hooks.commonButtonDisabled ? "text-light-gray" : "text-action-blue";
  const cursorStyle = hooks.commonButtonDisabled ? "" : " cursor-pointer";
  return (
    <>
      <Snackbar />
      <form
        ref={hooks.formRef}
        onSubmit={hooks.handleSubmit}
        className="flex justify-center items-center"
      >
        <div
          className={`w-11/12 mb-2 bg-[#ffffffcc] border border-dashed border-gray-300 rounded-md px-2 py-4 text-center ${cursorStyle}`}
          onClick={props.open}
        >
          <input {...props.getInputProps()} data-testid="file" />
          <div className="flex items-center justify-center">
            <PlusBoxIcon className="mr-3" color={hooks.buttonColor} />
            <p className={`${textColor} text-left whitespace-pre-wrap break-words`}>
              {props.buttonLabel}
            </p>
          </div>
        </div>
      </form>
    </>
  );
};

/**
 * ファイルアップローダーのメインコンポーネント
 * @param props - コンポーネントのプロパティ
 * @returns ファイルアップローダーのJSX要素
 */
const FileUploader = (props: Props) => {
  const hooks = useFileUploader(props.isUploadOnly);
  return <FileUploaderView props={props} hooks={hooks} />;
};

export default FileUploader;
