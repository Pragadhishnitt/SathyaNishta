/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    experimental: {
        turbo: {
            rules: {
                '*.svg': {
                    loaders: ['@svgr/webpack'],
                    as: '*.js',
                },
            },
        },
        // Optimize for faster development
        optimizeCss: true,
        optimizePackageImports: ['lucide-react'],
    },
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production',
        // Remove React devtools in production for faster builds
        reactRemoveProperties: process.env.NODE_ENV === 'production',
    },
    swcMinify: true,
    poweredByHeader: false,
    // Speed up development
    webpack: (config, { dev }) => {
        if (dev) {
            config.watchOptions = {
                poll: 1000,
                aggregateTimeout: 300,
                // Reduce file watching for better performance
                ignored: /node_modules/,
            };
            // Optimize module resolution
            config.resolve.alias = {
                ...config.resolve.alias,
                '@': '/src',
            };
        }
        return config;
    },
    // Reduce build overhead
    transpilePackages: [],
}

module.exports = nextConfig
