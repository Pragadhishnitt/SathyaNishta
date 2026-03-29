// NextAuth type extensions
import NextAuth from "next-auth"

declare module "next-auth" {
  interface Session {
    user?: {
      id?: string
      name?: string
      email?: string
      image?: string
      accessToken?: string  // Add accessToken property
    }
  }

  interface User {
    id?: string
    name?: string
    email?: string
    image?: string
    accessToken?: string  // Add accessToken property
  }
}
