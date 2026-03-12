// jest.config.jsでmoduleNameMapperとして登録するために作成。
export const getServerSession = jest.fn();

// NextAuthモック（handlers, auth, signIn, signOutを返す）
export default jest.fn(() => ({
  handlers: {},
  auth: jest.fn(),
  signIn: jest.fn(),
  signOut: jest.fn(),
}));
