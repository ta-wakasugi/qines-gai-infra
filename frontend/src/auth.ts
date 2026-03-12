import NextAuth, { type NextAuthConfig } from "next-auth";
import { JWT } from "next-auth/jwt";
import Keycloak from "next-auth/providers/keycloak";

/**
 * KEYCLOAK_URL の末尾スラッシュを除去して正規化する。
 * 未設定（undefined / 空文字 / 空白のみ）の場合は "" を返す。
 */
export const normalizeBaseUrl = (url?: string): string => {
  // undefined, null, 空文字, 空白のみ → 空文字を返す
  if (!url || url.trim() === "") return "";

  const trimmed = url.trim();
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
};

export const KC_BASE_URL = normalizeBaseUrl(process.env.KEYCLOAK_URL);
export const KC_REALM = process.env.KEYCLOAK_REALM;

async function refreshAccessToken(token: JWT) {
  try {
    const res = await fetch(
      `${KC_BASE_URL}/realms/${KC_REALM}/protocol/openid-connect/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          client_id: process.env.KEYCLOAK_CLIENT_ID!,
          client_secret: process.env.KEYCLOAK_SECRET!,
          grant_type: "refresh_token",
          refresh_token: token.refresh_token!,
        }),
        cache: "no-store",
      }
    );

    if (!res.ok) {
      const errBody = await res.text().catch(() => "");
      console.error(`[auth] refresh failed ${res.status} body=${errBody}`);
      return { ...token, error: "RefreshFailed" };
    }
    const data = await res.json();

    const next: JWT = {
      ...token,
      access_token: data.access_token,
      // Keycloakは設定によりRTローテーション有無が変わる。返ってきたら上書き。
      refresh_token: data.refresh_token ?? token.refresh_token,
      // expires_in は秒
      expires_at: Math.floor(Date.now() / 1000) + (data.expires_in ?? 300),
      error: undefined,
    };
    delete next.error;
    return next;
  } catch (e) {
    console.error(e);
    return { ...token, error: "RefreshFailed" };
  }
}

export const config = {
  providers: [
    Keycloak({
      clientId: process.env.KEYCLOAK_CLIENT_ID!,
      clientSecret: process.env.KEYCLOAK_SECRET!,
      issuer: `${KC_BASE_URL}/realms/${KC_REALM}`,
      checks: ["pkce"],
    }),
  ],
  callbacks: {
    authorized: async ({ auth }) => {
      return !!auth;
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) return `${baseUrl}${url}`;
      else if (new URL(url).origin === baseUrl) return url;
      return baseUrl;
    },
    async jwt({ token, account, user }) {
      // 新しいアカウントでのログイン時
      if (account) {
        return {
          access_token: account.access_token,
          refresh_token: account.refresh_token,
          expires_at: account.expires_at || Math.floor(Date.now() / 1000) + 300,
          iat: token.iat,
          exp: token.exp,
          jti: token.jti,
          email: user.email,
          id_token: account.id_token,
        };
      }

      if (!token.access_token) {
        return { error: "NoAccessToken" };
      }

      // 期限切れのときはリフレッシュ
      const now = Math.floor(Date.now() / 1000);
      const skew = 60; // 60秒前倒しで更新
      if (typeof token.expires_at === "number" && now >= token.expires_at - skew) {
        return await refreshAccessToken(token);
      }

      return token;
    },
    async session({ session, token }) {
      // エラー状態または空のトークンの場合
      if (token.error || Object.keys(token).length === 0) {
        // エラー情報を含むセッションを返す（クライアント側で適切にハンドリング）
        session.error = token.error || "InvalidSession";
        return session;
      }

      // アクセストークンが存在しない場合
      if (!token.access_token) {
        session.error = "NoAccessToken";
        return session;
      }

      // 正常なセッションの場合、トークン情報を追加
      session.access_token = token.access_token;
      session.refresh_token = token.refresh_token;
      session.id_token = token.id_token;

      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  trustHost: true,
} satisfies NextAuthConfig;

export const { handlers, auth, signIn, signOut } = NextAuth(config);
