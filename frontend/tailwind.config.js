/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                surface: {
                    0: '#050507',
                    1: '#0a0a0f',
                    2: '#0f0f17',
                    3: '#14141f',
                    4: '#1a1a2e',
                },
                neon: {
                    indigo: '#6366f1',
                    red: '#ef4444',
                    emerald: '#10b981',
                    amber: '#f59e0b',
                    cyan: '#06b6d4',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
            },
            animation: {
                'fade-in': 'fade-in 0.5s ease-out forwards',
                'slide-up': 'slide-in-up 0.5s ease-out forwards',
                'slide-right': 'slide-in-right 0.4s ease-out forwards',
                'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
                'radar-ping': 'radar-ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
                'shimmer': 'shimmer 2s infinite',
                'float': 'float 3s ease-in-out infinite',
                'spin-slow': 'spin-slow 8s linear infinite',
                'gradient-shift': 'gradient-shift 4s ease infinite',
            },
            boxShadow: {
                'neon-indigo': '0 0 15px rgba(99, 102, 241, 0.15), 0 0 30px rgba(99, 102, 241, 0.05)',
                'neon-red': '0 0 15px rgba(239, 68, 68, 0.15), 0 0 30px rgba(239, 68, 68, 0.05)',
                'neon-emerald': '0 0 15px rgba(16, 185, 129, 0.15), 0 0 30px rgba(16, 185, 129, 0.05)',
                'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
            },
        },
    },
    plugins: [],
}
