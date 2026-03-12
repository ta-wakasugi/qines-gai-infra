"use server";

/**
 * 指定されたパスからテキストファイルを取得します
 * @param path - テキストファイルのURLパス
 * @returns Promise<string> - テキストファイルの内容
 */
export const getText = async (path: string): Promise<string> => {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to fetch text file: ${response.statusText}`);
  }
  return await response.text();
};
