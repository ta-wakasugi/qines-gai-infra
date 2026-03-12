"use client";
import { getCollectionShareLink, getConversations } from "@/actions/collection";
import { useAccordion } from "@/hooks/useAccordion";
import { useError } from "@/hooks/useError";
import { CollectionBaseType } from "@/models/collection";
import { ConversationBaseType } from "@/models/conversation";
import { useState } from "react";
import { CollectionSettingMenu } from "./collectionSettingMenu";
import { deleteConversation, getConversationShareLink } from "@/actions/conversation";

/**
 * コレクションアコーディオンフック
 * @returns コレクション一覧の状態と操作関数を含むオブジェクト
 */
const useCollectionAccordion = (props: Props) => {
  const [conversations, setConversations] = useState<ConversationBaseType[] | null>(
    null
  );
  const { showError, errorTemplate } = useError();
  const accordionButtonSize = "8";
  const { isOpen, toggleAccordion, triggerIcon } = useAccordion(
    false,
    accordionButtonSize
  );

  /**
   * コレクションに紐づく会話一覧の取得、アコーディオン開閉
   */
  const handleGetConversations = async () => {
    toggleAccordion();
    if (isOpen || conversations !== null) {
      return;
    }
    try {
      const conversations: ConversationBaseType[] = await getConversations(
        props.collection.public_collection_id
      );
      setConversations(conversations);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    }
  };

  /**
   * コレクション共有リンクAPI実行
   * @returns 共有リンク情報
   */
  const handleShareCollection = async () => {
    return await getCollectionShareLink(props.collection.public_collection_id);
  };

  /**
   * 会話共有リンクAPI実行
   * @param conversationId - 会話ID
   * @returns 会話リンク情報
   */
  const handleShareConversation = async (conversationId: string) => {
    return await getConversationShareLink(conversationId);
  };

  /**
   * 会話削除API実行＋会話一覧から該当会話削除
   * @param conversationId - 会話ID
   */
  const handleDeleteConversation = async (conversationId: string) => {
    await deleteConversation(conversationId);
    if (conversations === null) {
      return;
    }
    const tempConversations = conversations.filter(
      (conversation) => conversation.public_conversation_id !== conversationId
    );
    setConversations(tempConversations);
  };

  return {
    conversations,
    isOpen,
    toggleAccordion,
    triggerIcon,
    handleGetConversations,
    handleShareCollection,
    handleShareConversation,
    handleDeleteConversation,
  };
};

type HooksType = ReturnType<typeof useCollectionAccordion>;

/**
 * コレクションアコーディオン表示
 * @param props
 * @param hooks
 * @returns 画面表示のJSX要素
 */
const CollectionAccordionView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: HooksType;
}) => {
  return (
    <>
      <div className="w-full m-2 bg-chat-area rounded-xl">
        <div className="flex items-center justify-between w-full bg-[#ffffffcc] p-3 rounded-xl shadow-[2px_2px_2px_#eee]">
          <div className="flex flex-1 items-center">
            <form action={hooks.handleGetConversations}>
              <button
                className="flex items-center text-left"
                data-testid="collectionAccordionButton"
              >
                {hooks.triggerIcon}
              </button>
            </form>
            <a
              className="ml-3 text-gray-600 hover:underline"
              href={`/collections/${props.collection.public_collection_id}`}
            >
              {props.collection.name}
            </a>
          </div>
          <div className="flex ml-2 items-center">
            <a
              className="border border-solid border-light-gray rounded-lg p-3 hover:bg-gray-100 mr-3"
              href={`/collections/${props.collection.public_collection_id}/chat/new`}
            >
              <div className="[font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal text-action-blue">
                新規チャット
              </div>
            </a>
            <CollectionSettingMenu
              deleteTitle="コレクション削除"
              deleteMessage={`${props.collection.name}\n上記コレクションを削除しますか？`}
              getShareLink={hooks.handleShareCollection}
              deleteItem={() =>
                props.handleDeleteCollection(props.collection.public_collection_id)
              }
            />
          </div>
        </div>
        {hooks.isOpen && (
          <div className="py-4 flex flex-col w-full items-start px-3 bg-chat-area rounded-xl">
            {hooks.conversations &&
              hooks.conversations.length > 0 &&
              hooks.conversations.map((conversation) => (
                <div
                  className="flex justify-between items-center gap-8 pl-6 pr-0 py-6 w-full relative"
                  key={conversation.public_conversation_id}
                >
                  <a
                    className="flex-1 max-w-full text-text text-base text-ellipsis overflow-hidden whitespace-nowrap hover:underline w-[20vw]"
                    href={`/collections/${props.collection.public_collection_id}/chat/${conversation.public_conversation_id}`}
                  >
                    {conversation.title}
                  </a>
                  <CollectionSettingMenu
                    deleteTitle="会話削除"
                    deleteMessage={`${conversation.title}\n上記会話を削除しますか？`}
                    getShareLink={() =>
                      hooks.handleShareConversation(conversation.public_conversation_id)
                    }
                    deleteItem={() =>
                      hooks.handleDeleteConversation(
                        conversation.public_conversation_id
                      )
                    }
                  />
                </div>
              ))}
            {!hooks.conversations ||
              (hooks.conversations.length === 0 && (
                <div className="pl-6 py-2">会話履歴がありません</div>
              ))}
          </div>
        )}
      </div>
    </>
  );
};

type Props = {
  collection: CollectionBaseType;
  handleDeleteCollection: (collectionId: string) => void;
};

/**
 * コレクションアコーディオンコンポーネント
 * @param props - コレクション情報
 * @param props.collection - コレクション情報
 * @param props.deleteCollection - コレクション削除関数
 * @returns JSX.Element
 */
export default function CollectionAccordion(props: Props) {
  const hooks = useCollectionAccordion(props);
  return <CollectionAccordionView props={props} hooks={hooks} />;
}
