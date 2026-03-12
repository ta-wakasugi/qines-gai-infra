import { CloseModalIcon } from "@/components/icons/closeModalIcon";
import { BaseModal } from "../baseModal";
import { THEME_COLORS } from "@/consts/color";

type Props = {
  isModalOpen: boolean;
  onClose: (result: boolean) => void;
  title: string;
  message: string;
};

/**
 * 削除確認モーダルのビューコンポーネント
 * @param props - モーダルのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns モーダルのJSX要素
 */
const DeleteConfirmModalView = ({ props }: { props: Props }) => {
  const className = "";
  return (
    <BaseModal isOpen={props.isModalOpen}>
      <div
        className={`flex flex-col w-[460px] items-center gap-6 pb-8 relative bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f] ${className}`}
        data-testid="delete-confirm-modal"
      >
        <div className="flex justify-end px-4 py-3 w-full bg-[#ffffffcc] rounded-[8px_8px_0px_0px] shadow-[0px_2px_12px_#aaaaaa1f] items-center relative]">
          <div className="flex items-center justify-between relative flex-1 grow">
            <div className="text-action-blue text-2xl tracking-[0.48px] relative [font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal">
              {props.title}
            </div>
            <div>
              <button onClick={() => props.onClose(false)}>
                <CloseModalIcon className="w-8 h-8" color={THEME_COLORS.button} />
              </button>
            </div>
          </div>
        </div>

        <div className="w-full">
          <div className="flex flex-col items-start gap-6 px-8 relative">
            <div className="flex items-center gap-2 relative w-full">
              <div className="text-lg tracking-[0.36px] relative [font-family:'Noto_Sans_JP-Regular',Helvetica] whitespace-pre-wrap break-words">
                {props.message}
              </div>
            </div>

            <div className="flex items-center justify-end gap-4 relative w-full w-24">
              <button
                className={`bg-orange-alert text-white rounded-lg px-5 py-3 text-lg`}
                onClick={() => props.onClose(true)}
                data-testid="deleteConfirmButton"
              >
                削除
              </button>
              <button
                className="border border-solid border-light-gray rounded-lg p-3 hover:bg-gray-100 text-action-blue"
                onClick={() => props.onClose(false)}
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      </div>
    </BaseModal>
  );
};

/**
 * 削除確認モーダルのメインコンポーネント
 * @param props - モーダルのプロパティ
 * @returns モーダルのJSX要素
 */
export const DeleteConfirmModal = (props: Props) => {
  return <DeleteConfirmModalView props={props} />;
};
