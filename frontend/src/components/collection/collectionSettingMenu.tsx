"use client";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import { BasePopupMenu } from "../popupMenu/basePopupMenu";
import { useSnackbar } from "@/hooks/useSnackbar";
import { useModal } from "@/hooks/useModal";
import { DeleteConfirmModal } from "../modal/collection/deleteConfirmModal";
import { useState } from "react";
import { SharedCollectionType } from "@/models/collection";
import { SharedConversationType } from "@/models/conversation";

type Props = {
  deleteTitle: string;
  deleteMessage: string;
  deleteItem: () => void;
  getShareLink: () => Promise<SharedCollectionType | SharedConversationType>;
};

/**
 * コレクション・会話設定のカスタムフック
 * @param {Props} props - メニューの表示状態と成果物情報
 */
const useCollectionSettingMenu = (props: Props) => {
  const { showError, errorTemplate } = useError();
  const { showSnackbar } = useSnackbar();
  const { isOpen, showModal, hideModal } = useModal();
  const { setCommonButtonDisabled, commonButtonDisabled } = useButtonDisabled();
  const [isVisibleCollectionMenu, setIsVisibleCollectionMenu] =
    useState<boolean>(false);

  /**
   * コレクション・会話共有APIを実行しクリップボードにコピーする
   */
  const handleShare = async () => {
    try {
      setCommonButtonDisabled(true);
      const res = await props.getShareLink();
      const snackbarMessage = "URLをコピーしました";
      navigator.clipboard.writeText(res.url).then(
        async () => {
          await showSnackbar(snackbarMessage);
        },
        () => {
          showError(errorTemplate.api);
        }
      );
      setIsVisibleCollectionMenu(false);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
    }
  };

  /**
   * コレクション・会話削除処理
   * @param confirmResult - 削除確認ダイアログの結果
   * @returns {Promise<void>}
   */
  const handleDelete = async (confirmResult: boolean) => {
    hideModal();
    if (confirmResult) {
      try {
        setCommonButtonDisabled(true);
        await props.deleteItem();
      } catch (e) {
        console.error(e);
        showError(errorTemplate.api);
      } finally {
        setCommonButtonDisabled(false);
      }
    }
  };

  /**
   * コレクション・会話削除の確認ダイアログを表示する
   */
  const confirmDelete = async (
    event: React.MouseEvent<HTMLButtonElement, MouseEvent>
  ) => {
    setIsVisibleCollectionMenu(false);
    showModal(event);
  };
  return {
    commonButtonDisabled,
    handleShare,
    confirmDelete,
    isOpen,
    handleDelete,
    isVisibleCollectionMenu,
    setIsVisibleCollectionMenu,
  };
};

/**
 * コレクション・会話設定メニューのビューコンポーネント
 * @param {object} param - プロパティとフック
 * @param {Props} param.props - メニューの表示状態と成果物情報
 * @param {ReturnType<typeof useCollectionSettingMenu>} param.hooks - useCollectionSettingMenuフックの戻り値
 */
const CollectionSettingMenuView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: ReturnType<typeof useCollectionSettingMenu>;
}) => {
  return (
    <>
      <button
        className="ml-3 p-1 hover:bg-gray-200 rounded-md focus:outline-none"
        onClick={() => hooks.setIsVisibleCollectionMenu(true)}
      >
        ･･･
      </button>
      <BasePopupMenu
        className="top-10 right-0"
        isVisible={hooks.isVisibleCollectionMenu}
        onClose={() => hooks.setIsVisibleCollectionMenu(false)}
      >
        <div className="flex-col items-start flex">
          <form
            action={hooks.handleShare}
            className="w-full hover:bg-gray-100 cursor-pointer border-gray-300 border-b"
          >
            <button
              className="py-1 px-8 w-full text-center text-action-blue"
              disabled={hooks.commonButtonDisabled}
            >
              共有
            </button>
          </form>
          <button
            className="py-1 px-8 w-full hover:bg-gray-100 cursor-pointer w-full text-center text-action-blue"
            onClick={hooks.confirmDelete}
            disabled={hooks.commonButtonDisabled}
          >
            削除
          </button>
        </div>
      </BasePopupMenu>
      <DeleteConfirmModal
        isModalOpen={hooks.isOpen}
        onClose={hooks.handleDelete}
        title={props.deleteTitle}
        message={props.deleteMessage}
      />
    </>
  );
};

/**
 * コレクション・会話設定のメインコンポーネント
 * @param {Props} props - メニューの表示状態
 * @returns メニューのJSX要素
 */
export const CollectionSettingMenu = (props: Props) => {
  const hooks = useCollectionSettingMenu(props);
  return <CollectionSettingMenuView props={props} hooks={hooks} />;
};
