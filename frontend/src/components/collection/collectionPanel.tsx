import { CollectionDetailType } from "@/models/collection";
import PanelDocumentCard from "../document/card/panelDocumentCard";
import { useState } from "react";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useCollection } from "@/hooks/collection/useCollection";
import { useDragDropUpload } from "@/hooks/useDragDropUpload";
import { DISPLAY_PATH } from "@/consts/paths";
import { NewChatIcon } from "../icons/newChatIcon";
import FileUploader from "../input/fileUploader";
import BackgroundUploadFilter from "../utils/BackgroundUploadFilter";
import { getConversations } from "@/actions/collection";
import { ConversationBaseType } from "@/models/conversation";
import { useError } from "@/hooks/useError";
import { useConversation } from "@/hooks/conversation/useConversation";

const PANEL_TYPE_COLLECTION = "panelCollection";
const PANEL_TYPE_CHAT = "panelChat";
type PanelType = typeof PANEL_TYPE_COLLECTION | typeof PANEL_TYPE_CHAT;

type Props = {
  collectionId: string;
  panelWidth: string;
};

/**
 * コレクションパネルのカスタムフック
 * @param {string} collectionId - コレクションID
 * @returns {Object} コレクションパネルの状態とメソッド
 */
const useCollectionPanel = (collectionId: string) => {
  const { showError, errorTemplate } = useError();
  const [panelType, setPanelType] = useState<PanelType>(PANEL_TYPE_COLLECTION);
  const [conversations, setConversations] = useState<ConversationBaseType[] | null>(
    null
  );
  const { conversationId } = useConversation();
  const { commonButtonDisabled, buttonColor } = useButtonDisabled();
  const { collection } = useCollection();
  const { getRootProps, getInputProps, isDragActive, open } = useDragDropUpload(
    panelType === PANEL_TYPE_CHAT
  );

  /**
   * 会話履歴を取得する
   * @returns {Promise<void>} なし
   */
  const getConversationHistories = async () => {
    setPanelType(PANEL_TYPE_CHAT);
    try {
      const response = await getConversations(collectionId);
      setConversations(response);
    } catch (error) {
      showError(errorTemplate.api);
    }
  };

  return {
    conversationId,
    conversations,
    getConversationHistories,
    panelType,
    setPanelType,
    commonButtonDisabled,
    buttonColor,
    collection,
    getRootProps,
    getInputProps,
    isDragActive,
    open,
  };
};

type HooksType = ReturnType<typeof useCollectionPanel>;

/** コレクションパネルのビューコンポーネント
 * @param {object} param - プロパティとフック
 * @param {Props} param.props - コレクションIDとパネル幅
 * @param {HooksType} param.hooks - useCollectionPanelフックの戻り値
 * @returns {JSX.Element} コレクションパネルのビュー
 */
const CollectionPanelView = ({ props, hooks }: { props: Props; hooks: HooksType }) => {
  /**
   * パネルのスタイルクラスを取得する
   * @param {PanelType} type - パネルの種類
   * @returns {string} スタイルクラス
   */
  const getPanelStyleClass = (type: PanelType) => {
    return type === hooks.panelType // 現在表示しているパネルの場合
      ? "bg-light-gray text-[#21282c]"
      : "text-pale-blue hover:bg-light-gray hover:cursor-pointer";
  };

  /** 左パネルのタブコンポーネント */
  const LeftPanelTab = () => {
    const tabs = [
      {
        type: PANEL_TYPE_COLLECTION,
        name: "ドキュメント",
        styleClass: getPanelStyleClass(PANEL_TYPE_COLLECTION),
        click: () => hooks.setPanelType(PANEL_TYPE_COLLECTION),
      },
      {
        type: PANEL_TYPE_CHAT,
        name: "会話履歴",
        styleClass: getPanelStyleClass(PANEL_TYPE_CHAT),
        click: hooks.getConversationHistories,
      },
    ];
    return (
      <div className="flex items-center gap-1 mx-3 mt-1 pb-2 border-b border-gray-300">
        {tabs.map((tab) => (
          <div
            key={tab.type}
            className={`w-1/2 px-1 py-2 rounded text-sm text-center ${tab.styleClass}`}
            onClick={tab.click}
          >
            {tab.name}
          </div>
        ))}
      </div>
    );
  };
  /** コレクション内のドキュメント一覧を表示するパネルコンポーネント */
  const DocumentCardList = (collection: CollectionDetailType) => {
    return collection.documents.length === 0 ? (
      <p>ドキュメントがありません</p>
    ) : (
      collection.documents.map((document, index) => (
        <PanelDocumentCard
          key={index}
          className="self-stretch w-11/12"
          document={document}
        />
      ))
    );
  };
  /** 会話履歴コンポーネント */
  const ConversationHistory = () => {
    if (!hooks.conversations) return null;
    return hooks.conversations.length === 0 ? (
      <p>会話履歴がありません</p>
    ) : (
      hooks.conversations.map((conversation, index) => (
        <div key={index} className="mx-3 w-11/12">
          {conversation.public_conversation_id === hooks.conversationId && (
            <p className="rounded-sm py-1 px-3 text-ellipsis overflow-hidden whitespace-nowrap bg-light-gray">
              {conversation.title}
            </p>
          )}
          {conversation.public_conversation_id !== hooks.conversationId && (
            <a
              className="block rounded-sm py-1 px-3 text-ellipsis overflow-hidden whitespace-nowrap hover:bg-light-gray"
              href={DISPLAY_PATH.CONVERSATION.CHAT(
                props.collectionId,
                conversation.public_conversation_id
              )}
            >
              {conversation.title}
            </a>
          )}
        </div>
      ))
    );
  };
  return (
    <>
      <div
        className="flex-wrap bg-transport mt-[38px] flex-1 flex flex-col overflow-hidden"
        {...hooks.getRootProps()}
      >
        <div className="flex flex-col w-full">
          <a
            className="w-fit text-action-blue hover:underline flex items-center p-2 ml-4"
            href={DISPLAY_PATH.CONVERSATION.NEW(props.collectionId)}
          >
            <NewChatIcon className="w-5 h-5 mr-2" color={hooks.buttonColor} />
            新規チャット
          </a>
          <LeftPanelTab />
        </div>
        <div className="flex-1 mt-2 w-full overflow-y-auto">
          {hooks.panelType === PANEL_TYPE_COLLECTION && hooks.collection && (
            <div
              className="flex flex-wrap justify-center gap-3 mb-3"
              data-testid="documentList"
            >
              <DocumentCardList {...hooks.collection} />
            </div>
          )}
          {hooks.panelType === PANEL_TYPE_CHAT && (
            <div className="flex flex-wrap justify-center gap-1" data-testid="chatList">
              <ConversationHistory />
            </div>
          )}
        </div>
        {hooks.panelType === PANEL_TYPE_COLLECTION && (
          <>
            <FileUploader
              getInputProps={hooks.getInputProps}
              buttonLabel="ドラッグでアップロード"
              isUploadOnly={false}
              open={hooks.open}
            />
            <BackgroundUploadFilter
              isDisplay={hooks.isDragActive}
              text="ドラッグでアップロード"
              className={`top-[40px] ${props.panelWidth}`}
            />
          </>
        )}
      </div>
    </>
  );
};

/** コレクションパネルのメインコンポーネント
 * @param {Props} props - コレクションIDとパネル幅
 * @returns {JSX.Element} コレクションパネルのビュー
 */
const CollectionPanel = (props: Props) => {
  const hooks = useCollectionPanel(props.collectionId);
  return <CollectionPanelView props={props} hooks={hooks} />;
};

export default CollectionPanel;
