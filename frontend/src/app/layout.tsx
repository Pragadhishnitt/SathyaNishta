import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { AuthProvider } from '@/components/AuthProvider'
import { ThreadProvider } from '@/context/ThreadContext'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
    title: 'MarketChatGPT by ET — Next-Gen Financial Intelligence',
    description: 'Advanced AI system for market analysis and financial forensics.',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark font-inter">
            <body className={`${inter.className} antialiased`}>
                <AuthProvider>
                    <ThreadProvider>
                        {children}
                    </ThreadProvider>
                </AuthProvider>
            </body>
        </html>
    )
}
