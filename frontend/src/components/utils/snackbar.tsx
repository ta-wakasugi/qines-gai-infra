import { useSnackbar } from "@/hooks/useSnackbar";
import { CheckCircleIcon } from "../icons/checkCircleIcon";

type Props = {
  className?: string;
  showCheckIcon?: boolean;
};

/**
 * スナックバーコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.className - スタイルクラス名
 * @returns コンポーネントJSX要素
 */
export default function Snackbar({ className, showCheckIcon = false }: Props) {
  const { snackbarMessage } = useSnackbar();
  if (!snackbarMessage) return null;
  return (
    <>
      <div
        className={`fixed right-0 left-0 top-3 z-20 px-2 py-1 bg-[#d8dfe166] rounded-md border border-action-blue m-auto w-fit ${className}`}
      >
        <div className="flex items-center">
          {showCheckIcon && <CheckCircleIcon className="mr-2" />}
          <div className="text-action-blue text-base tracking-[0.32px] leading-8 whitespace-nowrap">
            {snackbarMessage}
          </div>
        </div>
      </div>
    </>
  );
}
