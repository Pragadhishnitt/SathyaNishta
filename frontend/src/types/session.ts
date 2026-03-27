export interface User {
  id: string;
  email: string;
  name: string;
  image?: string | null;
  accessToken?: string;
}

export interface Session {
  user?: User | null;
  expires: string;
}

export interface JWT {
  accessToken: string;
  refreshToken?: string;
  expires: string;
}
