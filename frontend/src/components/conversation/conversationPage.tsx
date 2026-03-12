"use client";

import { getCollectionDetail } from "@/actions/collection";
import CollectionPanel from "@/components/collection/collectionPanel";
import { Conversation } from "@/components/conversation/conversation";
import { ErrorAlert } from "@/components/error/errorAlert";
import BaseHeader from "@/components/header/baseHeader";
import { THEME_COLORS } from "@/consts/color";
import { DISPLAY_PATH, QUERY_PARAMS } from "@/consts/paths";
import { useCollection } from "@/hooks/collection/useCollection";
import { usePanelDisplay } from "@/hooks/collection/usePanelDisplay";
import { useArtifact } from "@/hooks/conversation/useArtifact";
import { useConversation } from "@/hooks/conversation/useConversation";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useError } from "@/hooks/useError";
import { useReset } from "@/hooks/useReset";
import { useEffect } from "react";
import { BackIcon } from "../icons/backIcon";
import { RightPanelIcon } from "../icons/rightPanelIcon";
import Background from "../utils/Background";
import { ViewerContainer } from "./viewerContainer";
import { useSearchParams } from "next/navigation";
import { useConversationInput } from "@/hooks/conversation/useConversationInput";
import { getConversation } from "@/actions/conversation";
import { useConversationHistory } from "@/hooks/conversation/useConversationHistory";
import { useRecommendDocuments } from "@/hooks/conversation/useRecommendDocuments";
import PageLoading from "../loading/pageLoading";
import { useLoading } from "@/hooks/useLoading";

type Props = {
  collectionId: string;
  chatId?: string;
};

/**
 * 会話ページのカスタムフック
 * @param {Props} props - コレクションIDとチャットID
 */
const useConversationPage = (props: Props) => {
  const { showError, errorTemplate } = useError();
  const { showLoading, hideLoading } = useLoading();
  const { addConversationHistory } = useConversationHistory();
  const { setRecommendDocuments } = useRecommendDocuments();
  const { isPanelDisplay } = usePanelDisplay();
  const { collection, setCollection } = useCollection();
  const { base64Pdf } = usePdf();
  const { textContent } = usePlainText();
  const {
    artifact,
    latestArtifact,
    setArtifact,
    setLatestArtifact,
    addArtifactHistory,
  } = useArtifact();
  const { resetHooks } = useReset();
  const { setConversationId } = useConversation();
  const searchParams = useSearchParams();
  const { sendMessage } = useConversationInput();
  const isDisplayViewerContainer = Boolean(base64Pdf || textContent || artifact);
  const chatInnerWidth = isDisplayViewerContainer ? "w-full" : "w-3/5";
  const panelWidth = {
    collection: "",
    chat: "",
    artifact: "",
  };
  if (isPanelDisplay) {
    panelWidth.collection = isDisplayViewerContainer ? "w-[17%]" : "w-[17%]";
    panelWidth.chat = isDisplayViewerContainer ? "w-[33%]" : "w-[83%]";
    panelWidth.artifact = isDisplayViewerContainer ? "w-[50%]" : "";
  } else {
    panelWidth.chat = isDisplayViewerContainer ? "w-1/2" : "w-3/4";
    panelWidth.artifact = isDisplayViewerContainer ? "w-1/2" : "";
  }

  /**
   * 成果物を表示する処理
   */
  const openArtifact = () => {
    setArtifact(latestArtifact);
  };

  useEffect(() => {
    const fetchCollection = async () => {
      try {
        const collectionResponse = await getCollectionDetail(props.collectionId);
        setCollection(collectionResponse);
      } catch (error) {
        console.error(error);
        showError(errorTemplate.api);
      }
    };
    const fetchConversation = async (conversationId: string) => {
      showLoading();
      try {
        const conversationResponse = await getConversation({
          public_conversation_id: conversationId,
        });
        const messages = conversationResponse.messages;
        if (messages.length > 0) {
          addConversationHistory(messages);
          const recommendedDocuments =
            messages[messages.length - 1].metadata?.recommended_documents ?? null;
          setRecommendDocuments(recommendedDocuments);
        }
        const artifacts = conversationResponse.artifacts;
        if (artifacts.length > 0) {
          const latestArtifact = artifacts[artifacts.length - 1];
          setArtifact(latestArtifact);
          setLatestArtifact(latestArtifact);
          addArtifactHistory(artifacts);
        }
      } catch (error) {
        console.error(error);
        showError(errorTemplate.api);
      } finally {
        hideLoading();
      }
    };
    resetHooks();
    fetchCollection();
    const initialMessage = searchParams.get(QUERY_PARAMS.INITIAL_MESSAGE);
    if (props.chatId) {
      // 既存チャット
      setConversationId(props.chatId);
      fetchConversation(props.chatId);
    } else if (initialMessage) {
      // まずは聞いてみるからの遷移の場合、初期メッセージを送信する
      sendMessage({
        message: initialMessage,
        collectionId: props.collectionId,
      });
    }
  }, []);

  return {
    collection,
    isPanelDisplay,
    base64Pdf,
    artifact,
    isDisplayViewerContainer,
    chatInnerWidth,
    panelWidth,
    latestArtifact,
    openArtifact,
  };
};

type HooksType = ReturnType<typeof useConversationPage>;

/**
 * 会話ページのビューコンポーネント
 * @param {object} param - プロパティとフック
 * @param {Props} param.props - コレクションIDとチャットID
 * @param {HooksType} param.hooks - useConversationPageフックの戻り値
 */
export const ConversationPageView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: HooksType;
}) => {
  return (
    <>
      <PageLoading text="" />
      <Background className={`top-[40px] ${hooks.panelWidth.collection}`} />
      <Background
        className={`right-2 left-auto top-[40px] ${hooks.panelWidth.artifact}`}
      />
      <div className="relative flex flex-col h-screen">
        <ErrorAlert />
        <BaseHeader isPanelDisplay />
        <div className="h-9 absolute z-0 top-[38px] flex justify-between w-full">
          {hooks.collection && (
            <a
              href={DISPLAY_PATH.COLLECTION.EDIT(props.collectionId)}
              className={`${hooks.panelWidth.collection} pr-3 relative mt-1 inline-flex items-center text-action-blue hover:underline hover:cursor-pointer`}
            >
              <BackIcon color={THEME_COLORS.button} className="w-8 h-8" />
              <p className="m-w-[20vw] text-ellipsis overflow-hidden whitespace-nowrap">
                {hooks.collection.name}
              </p>
            </a>
          )}
          {!hooks.isDisplayViewerContainer && hooks.latestArtifact && (
            <p
              className="relative mr-3 text-sm inline-flex items-center text-action-blue hover:underline hover:cursor-pointer"
              onClick={hooks.openArtifact}
            >
              <RightPanelIcon className="w-5 h-5 mr-2" />
              成果物プレビュー
            </p>
          )}
        </div>
        <div className="flex flex-1 overflow-hidden">
          {/* コレクションパネル */}
          <div
            className={`${hooks.panelWidth.collection} justify-center bg-transport flex flex-col overflow-hidden`}
          >
            {hooks.isPanelDisplay && (
              <CollectionPanel
                collectionId={props.collectionId}
                panelWidth={hooks.panelWidth.collection}
              />
            )}
          </div>
          {/* チャット */}
          <div
            className={`${hooks.panelWidth.chat} bg-transport mb-1 mr-2 rounded-md flex-1 flex flex-col`}
          >
            <div
              className={`${hooks.chatInnerWidth} mx-auto mt-6 flex-1 flex flex-col overflow-hidden`}
            >
              <Conversation collectionId={props.collectionId} />
            </div>
          </div>
          {/* ビュワー */}
          {hooks.isDisplayViewerContainer && (
            <div
              className={`${hooks.panelWidth.artifact} flex-wrap bg-transport mb-1 mr-2 rounded-2xl bg-gray-100`}
            >
              <div className="mx-auto rounded-xl rounded-b-none">
                <ViewerContainer />
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

/**
 * 会話ページのメインコンポーネント
 * @param {object} param プロパティ
 * @param {Props} param.props - コレクションIDとチャットID
 */
export default function ConversationPage({ props }: { props: Props }) {
  const hooks = useConversationPage(props);
  return <ConversationPageView props={props} hooks={hooks} />;
}
