"use client";
import { useArtifact } from "@/hooks/conversation/useArtifact";
import { usePdf } from "@/hooks/pdf/usePdf";
import { ArtifactType } from "@/models/conversation";
import { OpenPdfIcon } from "../icons/openPdfIcon";

type Props = {
  artifacts: ArtifactType[];
};

/**
 * メッセージの成果物を表示し、プレビュー機能を提供するコンポーネント
 * @param {Props} props - 成果物の情報
 */
export const MessageArtifact = (props: Props) => {
  const { setArtifact } = useArtifact();
  const { resetPdf } = usePdf();

  /**
   * 成果物ビューワーを開く処理
   */
  const openArtifactViewer = (artifact: ArtifactType) => {
    resetPdf();
    setArtifact(artifact);
  };

  return (
    <>
      {props.artifacts.map((artifact, index) => (
        <div
          key={artifact.id || index}
          className="mt-2 mb-1 flex flex-col items-start gap-1 rounded-2xl"
        >
          <div className="flex flex-col items-start shadow-[0px_2px_8px_#eee] bg-[#ffffffcc] w-full self-stretch px-3 py-2 rounded-2xl">
            <div className="w-full flex self-stretch flex-[0_0_auto] flex-col items-end">
              <div className="flex w-full self-stretch items-center h-7 justify-between">
                <div className="flex-1 items-center text-ellipsis overflow-hidden whitespace-nowrap flex-1 w-[20vh]">
                  {artifact.title}
                </div>
                <div className="ml-1 mt-2 flex">
                  <button
                    className="ml-1"
                    data-testid="openPdfButton"
                    onClick={() => openArtifactViewer(artifact)}
                  >
                    <OpenPdfIcon className="w-6 h-6" color="blue" />
                  </button>
                </div>
              </div>
              <div
                className={`items-center flex-[0_0_auto] w-full flex self-stretch justify-between`}
                data-testid="cardCategoryArea"
              >
                <div className="flex self-stretch items-center grow flex-1 text-gray-400">
                  <div className="text-sm text-pale-blue font-normal leading-7 whitespace-nowrap">
                    Version: {artifact.version}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </>
  );
};
