"use server";

import { auth, signIn, KC_BASE_URL, KC_REALM, signOut } from "@/auth";
import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

const AUTH_PROVIDER = process.env.AUTH_PROVIDER;
const CLIENT_ID =
  process.env.AUTH_PROVIDER === "keycloak"
    ? process.env.KEYCLOAK_CLIENT_ID || ""
    : process.env.COGNITO_CLIENT_ID || "";

// Cognito用定数
const LOGOUT_REDIRECT_URL = process.env.LOGOUT_REDIRECT_URL || "/";
const COGNITO_BASE_URL = process.env.COGNITO_BASE_URL;
const SESSION_COOKIE = process.env.ALB_SESSION_COOKIE_NAME || "AWSELBAuthSessionCookie";

/**
 * JWTトークンをデコードする
 *
 * セキュリティ注意: このJWTデコードは検証なしの情報表示目的のみ
 * 実際の認証・認可はバックエンドで行われる
 *
 * @param token - デコード対象のJWTトークン
 * @returns デコードされたペイロード、失敗時はnull
 */
const decodeJWT = (token: string) => {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) {
      throw new Error("Invalid JWT format");
    }
    const payload = parts[1];
    const decodedPayload = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decodedPayload);
  } catch (e) {
    return null;
  }
};

/**
 * 認証トークンを取得する。
 *
 * Keycloak認証の場合はNextAuthセッションからアクセストークンを取得し、
 * Cognito認証の場合はALBヘッダーからアクセストークンを取得する。
 *
 * @returns 認証トークン（存在しない場合は空文字列）
 */

export const getAuthToken = async () => {
  if (AUTH_PROVIDER === "keycloak") {
    try {
      const session = await auth();

      if (session?.access_token) {
        const token = session.access_token as string;
        return token;
      }

      return "";
    } catch (error) {
      return "";
    }
  }

  const h = headers();
  const token = h.get("x-amzn-oidc-accesstoken");
  return token || "";
};

/**
 * ユーザー名を取得する
 * @returns ユーザー名（取得できない場合は"Anonymous"）
 */
export const getUsername = async () => {
  const notFoundUsername = "Anonymous";

  if (AUTH_PROVIDER === "keycloak") {
    const session = await auth();
    return session?.user?.email ?? notFoundUsername;
  }

  // Cognito認証の場合
  const h = headers();
  const oidcData = h.get("x-amzn-oidc-data");
  if (!oidcData) return notFoundUsername;

  const decoded = decodeJWT(oidcData);
  return decoded.email ?? notFoundUsername;
};

/**
 * ログイン処理を実行
 */
export const login = async (callbackUrl: string) => {
  await signIn("keycloak", { redirectTo: callbackUrl });
};

/**
 * ログアウト処理を実行する
 * 全ての認証関連クッキーを削除する
 */
export const logout = async () => {
  if (AUTH_PROVIDER === "keycloak") {
    // セッションを破棄する前にid_tokenを保存
    const session = await auth();
    const idToken = session?.id_token;

    // アプリ側のセッションを破棄
    await signOut({ redirect: false });

    // KeyCloak RP-Logout
    const issuer = `${KC_BASE_URL}/realms/${KC_REALM}`;
    const logoutUrl = new URL(`${issuer}/protocol/openid-connect/logout`);

    if (idToken) {
      logoutUrl.searchParams.set("id_token_hint", idToken);
    }

    // Keycloakのログアウト後、NextAuthのサインアウトエンドポイントを経由してホームへ
    const baseUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";
    logoutUrl.searchParams.set("post_logout_redirect_uri", baseUrl);

    // Keycloakのグローバルログアウトにリダイレクト
    redirect(logoutUrl.toString());
  } else {
    // Cognito認証の場合
    // 最大４つに分割されたALBの認証Cookieを失効
    const names = [
      SESSION_COOKIE,
      `${SESSION_COOKIE}-0`,
      `${SESSION_COOKIE}-1`,
      `${SESSION_COOKIE}-2`,
      `${SESSION_COOKIE}-3`,
      "AWSALBAuthNonce",
    ];

    const c = cookies();
    for (const name of names) {
      // 有効期限を過去にして、Path属性を揃えた上で上書き
      c.set({
        name,
        value: "",
        path: "/",
        httpOnly: true,
        secure: true,
        sameSite: "none",
        expires: new Date(0),
      });
    }

    const url = new URL("/logout", COGNITO_BASE_URL);

    url.searchParams.set("client_id", CLIENT_ID);
    url.searchParams.set("logout_uri", LOGOUT_REDIRECT_URL);
    redirect(url.toString());
  }
};
