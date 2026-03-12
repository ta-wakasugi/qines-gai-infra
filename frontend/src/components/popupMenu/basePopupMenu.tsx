import { ReactNode, useEffect, useRef } from "react";

type Props = {
  isVisible: boolean;
  onClose: () => void;
  className: string;
  children: ReactNode;
};

/**
 * ベースポップアップメニューのカスタムフック
 * @param props - ポップアップメニューのプロパティ
 * @returns メニューの参照を含むオブジェクト
 */
const useBasePopupMenu = (props: Props) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    /**
     * 外部クリック時のイベントハンドラー
     * @param event - マウスイベント
     */
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        props.onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
  }, [props]);

  return {
    ref,
  };
};

type Hooks = ReturnType<typeof useBasePopupMenu>;

/**
 * ベースポップアップメニューのビューコンポーネント
 * @param props - ポップアップメニューのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns ポップアップメニューのJSX要素
 */
const BasePopupMenuView = ({ props, hooks }: { props: Props; hooks: Hooks }) => {
  if (!props.isVisible) {
    return null;
  }

  return (
    <>
      <div
        ref={hooks.ref}
        className={`absolute z-10 shadow-lg border rounded-md ${props.className}`}
        data-testid="popupMenu"
      >
        <div className="inline-flex items-start px-0 bg-white rounded-md">
          {props.children}
        </div>
      </div>
    </>
  );
};

/**
 * ベースポップアップメニューのメインコンポーネント
 * @param props - ポップアップメニューのプロパティ
 * @returns ポップアップメニューのJSX要素
 */
export const BasePopupMenu = (props: Props) => {
  const hooks = useBasePopupMenu(props);
  return <BasePopupMenuView props={props} hooks={hooks} />;
};
