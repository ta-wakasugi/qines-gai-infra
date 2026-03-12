"use client";
import { ArtifactType, ContextType } from "@/models/conversation";
import { AgentIcon } from "../icons/agentIcon";
import MdPreview from "../markdown/mdPreview";
import { MessageArtifact } from "./messageArtifact";
import { MessageReference } from "./messageReference";

type Props = {
  message: string;
  disabled: boolean;
  references?: ContextType[] | null;
  artifacts?: ArtifactType[] | null;
};

/**
 * AIエージェントのメッセージを表示するコンポーネント。
 * Markdownフォーマットのメッセージ、参考文献、成果物を表示する
 */
export const AgentMessage = (props: Props) => {
  return (
    <>
      <div
        className="flex items-start gap-5 self-stretch w-11/12 flex-[0_0_auto] justify-self-center"
        data-testid="agentMessage"
      >
        <button className="mt-2" disabled={props.disabled}>
          <AgentIcon className="w-8 h-8" />
        </button>
        <div className="flex-col items-start gap-3 py-3 px-[20px] flex-1 grow bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f]">
          <MdPreview source={props.message} />
          {props.artifacts && <MessageArtifact artifacts={props.artifacts} />}
          {props.references && <MessageReference references={props.references} />}
        </div>
      </div>
    </>
  );
};
