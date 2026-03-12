"use client";
import { getUsername } from "@/actions/auth";
import { useArtifact } from "@/hooks/conversation/useArtifact";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { MessageType } from "@/models/conversation";
import { ArtifactType } from "@/models/conversation";
import { useEffect, useState } from "react";
import { UserIcon } from "../icons/userIcon";
import { AgentMessage } from "./agentMessage";

type Props = {
  conversation: MessageType;
};

/**
 * 会話履歴のカスタムフック
 * ボタンの無効化状態、成果物の取得、ユーザー名の管理を行う
 * @returns {object} フックで管理する状態と操作メソッド
 */
const useHookConversationHistory = () => {
  const { commonButtonDisabled } = useButtonDisabled();
  const { getArtifactByIdAndVersion } = useArtifact();

  /**
   * 会話から成果物情報を取得する
   * メタデータから成果物IDとバージョンを抽出し、対応する成果物を返す
   * @param {MessageType} conversation - 会話データ
   * @returns {ArtifactType[] | null} 成果物情報またはnull
   */
  const getArtifact = (conversation: MessageType) => {
    if (
      !conversation.metadata ||
      !conversation.metadata.generated_artifacts ||
      conversation.metadata.generated_artifacts.length === 0
    ) {
      return null;
    }
    const validArtifacts: ArtifactType[] =
      conversation.metadata.generated_artifacts.flatMap((artifact) => {
        const result = getArtifactByIdAndVersion(artifact.id, artifact.version);
        return result ? [result] : [];
      });

    return validArtifacts.length > 0 ? validArtifacts : null;
  };

  /**
   * ユーザー名を非同期で取得し状態を更新
   */
  const [username, setUsername] = useState("");
  useEffect(() => {
    (async () => {
      const tempName = await getUsername();
      setUsername(tempName);
    })();
  }, []);

  return { commonButtonDisabled, getArtifact, username };
};

type HooksType = ReturnType<typeof useHookConversationHistory>;

/**
 * 会話履歴のビューコンポーネント
 * ユーザーメッセージとエージェントメッセージを表示形式を切り替えて表示
 * @param {object} param - プロパティとフック
 * @param {Props} param.props - 会話データ
 * @param {HooksType} param.hooks - useHookConversationHistoryフックの戻り値
 */
const ConversationHistoryView = ({
  props,
  hooks,
}: {
  props: Props;
  hooks: HooksType;
}) => {
  /**
   * ユーザーメッセージ表示用のサブコンポーネント
   * アイコンとメッセージ内容を表示
   * @param {string} message - メッセージ内容
   * @returns {JSX.Element} ユーザーメッセージの表示要素
   */
  const UserMessageView = (message: string) => {
    return (
      <div className="flex flex-col items-start w-11/12 justify-self-center overflow-hidden">
        <div className="inline-flex items-center justify-center gap-1 pl-[60px] pr-0 py-0 flex-[0_0_auto] w-full">
          <div className="w-fit mt-1 [font-family:'Hiragino_Sans-W4',Helvetica] font-normal text-sm text-base whitespace-nowrap text-ellipsis overflow-hidden text-gray-400 w-full">
            {hooks.username}
          </div>
        </div>
        <div
          className="flex items-start gap-5 self-stretch w-full flex-[0_0_auto]"
          data-testid="userMessage"
        >
          <UserIcon className="flex-col mt-2 w-8 h-8" />
          <div className="flex-col items-start gap-3 py-3 px-[20px] flex-1 grow bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f] whitespace-break-spaces">
            {message}
          </div>
        </div>
      </div>
    );
  };

  if (props.conversation.role === "user") {
    return UserMessageView(props.conversation.content);
  }
  const metadata = props.conversation?.metadata ?? null;
  const references = metadata?.contexts ?? null;
  return (
    <AgentMessage
      message={props.conversation.content}
      disabled={hooks.commonButtonDisabled}
      references={references}
      artifacts={hooks.getArtifact(props.conversation)}
    />
  );
};

/**
 * 会話履歴のメインコンポーネント
 * フックとビューを統合して会話履歴を表示
 * @param {Props} props - 会話データ
 * @returns {JSX.Element} 会話履歴の表示要素
 */
export const ConversationHistory = (props: Props) => {
  const hooks = useHookConversationHistory();
  return <ConversationHistoryView props={props} hooks={hooks} />;
};
