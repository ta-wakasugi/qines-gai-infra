import type { Session } from "next-auth";

export const useSession = jest.fn((): { data: Session | null; status: string } => ({
  data: { user: { name: "Test User", email: "test@example.com" } } as Session,
  status: "authenticated",
}));

export const signIn = jest.fn();
export const signOut = jest.fn();
