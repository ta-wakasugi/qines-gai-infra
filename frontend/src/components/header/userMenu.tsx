import { BasePopupMenu } from "../popupMenu/basePopupMenu";
import { logout } from "@/actions/auth";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

interface MenuType {
  label: string;
  action: () => void;
}

/**
 * ユーザーメニューコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.isOpen - メニューの表示状態
 * @param props.onClose - メニューを閉じる際のコールバック関数
 * @returns ユーザーメニューのJSX要素
 */
const UserMenu = (props: Props) => {
  const menus: MenuType[] = [
    {
      label: "ログアウト",
      action: logout,
    },
  ];

  return (
    <BasePopupMenu
      isVisible={props.isOpen}
      onClose={props.onClose}
      className="absolute top-10 right-2 z-10 shadow-lg border rounded-lg"
    >
      {menus.map((menu, index) => (
        <form key={menu.label} action={menu.action}>
          <button
            className={`items-center gap-2.5 px-2 py-1 w-full ${index === menus.length - 1 ? "" : "border-b"}`}
          >
            <div className="[font-family:'Noto_Sans-Bold',Helvetica] ">
              {menu.label}
            </div>
          </button>
        </form>
      ))}
    </BasePopupMenu>
  );
};

export default UserMenu;
