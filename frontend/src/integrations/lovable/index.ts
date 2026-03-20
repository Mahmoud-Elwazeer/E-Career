// Stub — no backend integration in frontend-only mode

export const lovable = {
  auth: {
    signInWithOAuth: async (_provider: string, _opts?: any) => {
      return { redirected: false, error: null };
    },
  },
};
