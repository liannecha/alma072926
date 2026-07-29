import type { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    googleIdToken?: string;
    user?: DefaultSession['user'];
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    googleIdToken?: string;
  }
}
