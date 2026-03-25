import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { AuthProvider } from '@/components/AuthProvider'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
    title: 'Sathya Nishta — AI Forensic Investigation Platform',
    description: 'Multi-agent AI system for financial fraud detection, compliance verification, and forensic investigation powered by LangGraph.',
    keywords: ['fraud detection', 'financial investigation', 'AI forensics', 'compliance'],
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.className} antialiased`}>
                <AuthProvider>
                    {children}
                </AuthProvider>
            </body>
        </html>
    )
}
