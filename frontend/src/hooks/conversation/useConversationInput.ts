import { useStreamingMessage } from "@/hooks/conversation/useStreamingMessage";
import { useError } from "@/hooks/useError";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useRecommendDocuments } from "@/hooks/conversation/useRecommendDocuments";
import { useArtifact } from "@/hooks/conversation/useArtifact";
import { useConversation } from "@/hooks/conversation/useConversation";
import { useConversationHistory } from "@/hooks/conversation/useConversationHistory";
import { ChatRequestType, MessageType } from "@/models/conversation";
import { postConversation } from "@/actions/postConversation";
import { DISPLAY_PATH } from "@/consts/paths";
import { atom, useAtom } from "jotai";

type Props = {
  message: string;
  collectionId: string;
};

const inputMessageAtom = atom<string>("");

/**
 * 会話入力に関する状態と操作を管理するカスタムフック
 */
export const useConversationInput = () => {
  const [inputMessage, setInputMessage] = useAtom(inputMessageAtom);
  const { setCommonButtonDisabled } = useButtonDisabled();
  const { showError, errorTemplate } = useError();
  const { setStreamingMessage } = useStreamingMessage();
  const { setRecommendDocuments } = useRecommendDocuments();
  const { setArtifact, setLatestArtifact, addArtifactHistory } = useArtifact();
  const { conversationId, setConversationId } = useConversation();
  const { addConversationHistory, removeLastConversationHistory } =
    useConversationHistory();

  /**
   * 会話APIを呼び出す関数
   * @param props - 会話APIに必要なプロパティ
   */
  const postConversationApi = async (props: Props) => {
    try {
      const requestParams = {
        message: props.message,
        public_collection_id: props.collectionId,
      } as ChatRequestType;
      if (conversationId) {
        requestParams.public_conversation_id = conversationId;
      }
      const response = await postConversation(
        requestParams,
        setStreamingMessage,
        setArtifact,
        addArtifactHistory
      );
      const agentMessage = response.message;
      const artifact = response.artifact ?? null;
      const recommendedDocuments = agentMessage.metadata?.recommended_documents ?? null;
      addConversationHistory(agentMessage);
      setRecommendDocuments(recommendedDocuments);
      setArtifact(artifact);
      setLatestArtifact(artifact);
      addArtifactHistory(artifact);
      if (!conversationId) {
        const redirectPath = DISPLAY_PATH.CONVERSATION.CHAT(
          props.collectionId,
          response.public_conversation_id
        );
        // routerを使用すると画面が再描画されてReset処理が走るためURLの書き換えだけを行う
        history.replaceState(null, "", redirectPath);
        setConversationId(response.public_conversation_id);
      }
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
      removeLastConversationHistory();
      setInputMessage(props.message);
    } finally {
      setCommonButtonDisabled(false);
      setStreamingMessage("");
    }
  };

  /**
   * メッセージ送信を処理する関数
   * @param props - メッセージ送信に必要なプロパティ
   */
  const sendMessage = async (props: Props) => {
    setCommonButtonDisabled(true);
    const userMessage: MessageType = {
      content: props.message,
      metadata: {},
      role: "user",
    };
    addConversationHistory(userMessage);
    setInputMessage(""); // 送信後に入力欄をクリア
    postConversationApi(props);
  };

  return {
    inputMessage,
    setInputMessage,
    sendMessage,
  };
};
