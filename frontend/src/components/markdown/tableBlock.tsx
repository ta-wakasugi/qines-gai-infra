interface Props {
  children: React.ReactNode;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

/**
 * テーブルブロックを表示するコンポーネント
 * @param {Props} props - コンポーネントのプロパティ
 * @returns {JSX.Element} テーブルブロック要素
 */
const TableBlock = ({ children, ...props }: Props) => (
  <div className="scroll-container">
    <table {...props}>{children}</table>
  </div>
);

export default TableBlock;
