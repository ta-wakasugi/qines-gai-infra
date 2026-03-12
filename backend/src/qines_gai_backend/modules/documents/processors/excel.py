import os
import openpyxl
from typing import List
from langchain_core.documents import Document

class ExcelProcessor:
    """Excelファイル（.xlsx）をRAG向けに最適化して読み込むプロセッサ"""

    def process(self, file_path: str, original_filename: str = None) -> List[Document]:
        """
        Excelファイルを解析し、1行を1つのDocumentとして返す。
        
        Args:
            file_path (str): 解析対象のExcelファイルのパス
            
        Returns:
            List[Document]: LangChainのDocumentオブジェクトのリスト
        """
        documents = []
        filename = original_filename if original_filename else os.path.basename(file_path)

        try:
            # data_only=Trueで数式の計算結果を取得
            wb = openpyxl.load_workbook(file_path, data_only=True)
            
            for sheet_idx, sheet_name in enumerate(wb.sheetnames):
                ws = wb[sheet_name]
                
                # 非表示シートはスキップ
                if ws.sheet_state == 'hidden':
                    continue
                    
                max_r = ws.max_row
                max_c = ws.max_column

                # 空シートはスキップ
                if max_r == 1 and max_c == 1 and ws.cell(1,1).value is None:
                    continue

                # 0. 非表示行の特定
                hidden_rows = set()
                for r_idx, row_dim in ws.row_dimensions.items():
                    if row_dim.hidden:
                        hidden_rows.add(r_idx)

                # 1. マトリックス構築とセル結合の展開
                matrix = [[None for _ in range(max_c)] for _ in range(max_r)]
                for r in range(1, max_r + 1):
                    for c in range(1, max_c + 1):
                        matrix[r-1][c-1] = ws.cell(row=r, column=c).value
                        
                for merged_range in ws.merged_cells.ranges:
                    min_c, min_r, max_c_merge, max_r_merge = merged_range.bounds
                    top_left_val = ws.cell(row=min_r, column=min_c).value
                    for r in range(min_r, max_r_merge + 1):
                        for c in range(min_c, max_c_merge + 1):
                            matrix[r-1][c-1] = top_left_val

                # 2. 表の開始位置（ヘッダー）の自動検知
                header_start_idx = -1
                MIN_UNIQUE_COLS_FOR_TABLE = 3 
                
                for i, row in enumerate(matrix):
                    r_excel = i + 1
                    if r_excel in hidden_rows: continue
                    
                    unique_vals = set(str(v).strip() for v in row if v is not None and str(v).strip() != "")
                    if len(unique_vals) >= MIN_UNIQUE_COLS_FOR_TABLE:
                        header_start_idx = i
                        break
                        
                if header_start_idx == -1:
                    continue # 表が見つからないシートはスキップ

                # 3. ヘッダーの階層検知
                header_end_idx = header_start_idx
                for merged_range in ws.merged_cells.ranges:
                    min_c, min_r, max_c_merge, max_r_merge = merged_range.bounds
                    if min_r - 1 <= header_start_idx <= max_r_merge - 1:
                        if (max_r_merge - 1) > header_end_idx:
                            header_end_idx = max_r_merge - 1

                # 4. メタデータ（説明文）抽出
                metadata_lines = []
                for i in range(header_start_idx):
                    r_excel = i + 1
                    if r_excel in hidden_rows: continue
                    
                    row_vals = []
                    for v in matrix[i]:
                        val_str = str(v).strip()
                        if v is not None and val_str != "" and val_str not in row_vals:
                            row_vals.append(val_str)
                    if row_vals:
                        metadata_lines.append(" ".join(row_vals))
                metadata_text = "\n".join(metadata_lines)

                # 5. ヘッダー平坦化
                flat_headers = []
                for c in range(max_c):
                    col_header_parts = []
                    for r in range(header_start_idx, header_end_idx + 1):
                        val = matrix[r][c]
                        if val is not None and str(val).strip() != "":
                            val_str = str(val).strip().replace('\n', '')
                            if not col_header_parts or col_header_parts[-1] != val_str:
                                col_header_parts.append(val_str)
                    flat_headers.append("_".join(col_header_parts) if col_header_parts else f"列{c+1}")

                # 6. データ行抽出とLangChain Document化
                for r in range(header_end_idx + 1, max_r):
                    r_excel = r + 1
                    if r_excel in hidden_rows: continue
                        
                    row_data = matrix[r]
                    unique_data_vals = set(str(v).strip() for v in row_data if v is not None and str(v).strip() != "")
                    if len(unique_data_vals) < 2:
                        continue # フィルタ用の空行などはスキップ
                        
                    lines = []
                    lines.append(f"■ファイル名: {filename}")
                    lines.append(f"■シート名: {sheet_name}")
                    if metadata_text:
                        lines.append(f"■シート前提情報:\n{metadata_text}\n")
                        
                    for c in range(max_c):
                        header = flat_headers[c]
                        val = row_data[c]
                        val_str = "(空欄)" if val is None or str(val).strip() == "" else str(val).strip().replace('\n', ' ')
                        lines.append(f"{header}: {val_str}")
                        
                    page_content = "\n".join(lines)
                    
                    # 1行のデータを1つのLangChain Documentとして作成
                    # メタデータにシート番号（page_numとして代用）を付与
                    doc = Document(
                        page_content=page_content,
                        metadata={
                            "source": file_path,
                            "page_num": sheet_idx + 1,
                            "sheet_name": sheet_name,
                            "total_pages": len(wb.sheetnames)
                        }
                    )
                    documents.append(doc)

        except Exception as e:
            # エラーロギング（既存のloggerがあればそれを使用してください）
            print(f"Excel処理中にエラーが発生しました: {e}")
            raise

        return documents