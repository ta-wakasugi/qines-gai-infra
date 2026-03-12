import { createCollection, updateCollection } from "@/actions/collection";
import { SaveButton } from "@/components/button/saveButton";
import { CloseModalIcon } from "@/components/icons/closeModalIcon";
import { DISPLAY_PATH } from "@/consts/paths";
import { useCollection } from "@/hooks/collection/useCollection";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { BaseModal } from "../baseModal";
import { useLoading } from "@/hooks/useLoading";

type Props = {
  isModalOpen: boolean;
  handleCloseModal: () => void;
  documentIds: string[];
};

const buttonSaveId = "btn_save";
const buttonNewChat = "btn_new_chat";

/**
 * コレクション保存モーダルのカスタムフック
 * @param props - モーダルのプロパティ
 * @returns モーダルの状態と操作関数を含むオブジェクト
 */
const useSaveCollectionModal = (props: Props) => {
  const { collection, setCollection } = useCollection();
  const collectionName = collection?.name ?? "";
  const isEdit = collectionName !== "";
  const [inputMessage, setInputMessage] = useState<string>("");
  const { showLoading, hideLoading, setLoadingText } = useLoading();
  const { commonButtonDisabled, setCommonButtonDisabled, buttonColor } =
    useButtonDisabled();
  const { errorTemplate, showError } = useError();
  const buttonDisabled = inputMessage === "" || commonButtonDisabled;
  const router = useRouter();

  useEffect(() => {
    setInputMessage(collectionName);
  }, [collectionName]);

  /**
   * モーダルを閉じる関数
   */
  const closeModal = () => {
    setInputMessage(collectionName);
    props.handleCloseModal();
  };

  /**
   * コレクションを保存する関数
   * @param name - コレクション名
   * @returns 保存したコレクション情報
   */
  const handleSaveCollection = async (name: string) => {
    const requestParams = {
      name: name,
      document_ids: props.documentIds,
    };
    const saveCollection = isEdit
      ? await updateCollection(collection?.public_collection_id ?? "", requestParams)
      : await createCollection(requestParams);
    setCollection(saveCollection);
    return saveCollection;
  };

  /**
   * フォーム送信を処理する関数
   * @param e - フォームイベント
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    showLoading();
    setLoadingText("コレクション保存中...");
    setCommonButtonDisabled(true);
    const clickId = (e.nativeEvent as SubmitEvent).submitter?.id;
    try {
      const saveCollection = await handleSaveCollection(inputMessage);
      props.handleCloseModal();
      if (clickId === buttonNewChat) {
        router.push(DISPLAY_PATH.CONVERSATION.NEW(saveCollection.public_collection_id));
      } else {
        router.push(DISPLAY_PATH.COLLECTION.EDIT(saveCollection.public_collection_id));
      }
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hideLoading();
    }
  };

  return {
    inputMessage,
    setInputMessage,
    setCommonButtonDisabled,
    buttonColor,
    buttonDisabled,
    handleSubmit,
    closeModal,
  };
};

type HooksType = ReturnType<typeof useSaveCollectionModal>;

/**
 * コレクション保存モーダルのビューコンポーネント
 * @param props - モーダルのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns モーダルのJSX要素
 */
const SaveCollectionModalView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: HooksType;
}) => {
  const className = "";
  return (
    <BaseModal isOpen={props.isModalOpen}>
      <div
        className={`flex flex-col w-[460px] items-center gap-6 pb-8 relative bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f] ${className}`}
        data-testid="save-collection-modal"
      >
        <div className="flex justify-end px-4 py-3 w-full bg-[#ffffffcc] rounded-[8px_8px_0px_0px] shadow-[0px_2px_12px_#aaaaaa1f] items-center relative]">
          <div className="flex items-center justify-between relative flex-1 grow">
            <div className="text-action-blue text-2xl tracking-[0.48px] relative [font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal">
              コレクションを保存
            </div>
            <div>
              <button onClick={hooks.closeModal}>
                <CloseModalIcon className="w-8 h-8" color={hooks.buttonColor} />
              </button>
            </div>
          </div>
        </div>

        <div className="w-full">
          <form onSubmit={hooks.handleSubmit}>
            <div className="flex flex-col items-start gap-6 px-8 relative">
              <div className="flex flex-col items-start justify-center gap-1 relative w-full bg-[#ffffffcc] border border-solid border-[#d8e1df] shadow-[inset_0px_2px_6px_#aaaaaa1f]">
                <div className="text-lg tracking-[0.36px] leading-9 relative w-full [font-family:'Noto_Sans_JP-Regular',Helvetica]">
                  <input
                    type="text"
                    className="w-full p-2 outline-none bg-transparent"
                    placeholder="コレクション名"
                    value={hooks.inputMessage}
                    onChange={(e) => hooks.setInputMessage(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 relative w-full">
                <div className="text-lg tracking-[0.36px] relative [font-family:'Noto_Sans_JP-Regular',Helvetica]">
                  ドキュメント数：
                </div>

                <div className="relative [font-family:'Noto_Sans_JP-Regular',Helvetica] text-lg">
                  {props.documentIds.length} 件
                </div>
              </div>

              <div className="flex items-center justify-end gap-4 relative w-full">
                <SaveButton
                  className="w-24"
                  id={buttonSaveId}
                  disabled={hooks.buttonDisabled}
                >
                  保存
                </SaveButton>
                <SaveButton
                  className="w-56"
                  id={buttonNewChat}
                  disabled={hooks.buttonDisabled}
                >
                  保存して新規チャット
                </SaveButton>
              </div>
            </div>
          </form>
        </div>
      </div>
    </BaseModal>
  );
};

/**
 * コレクション保存モーダルのメインコンポーネント
 * @param props - モーダルのプロパティ
 * @returns モーダルのJSX要素
 */
export const SaveCollectionModal = (props: Props) => {
  const hooks = useSaveCollectionModal(props);
  return <SaveCollectionModalView props={props} hooks={hooks} />;
};
