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
    },
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production',
    },
    swcMinify: true,
    poweredByHeader: false,
    // Speed up development
    webpack: (config, { dev }) => {
        if (dev) {
            config.watchOptions = {
                poll: 1000,
                aggregateTimeout: 300,
            };
        }
        return config;
    },
}

module.exports = nextConfig
