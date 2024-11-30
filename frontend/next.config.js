const CopyPlugin = require("copy-webpack-plugin");
/** @type {import('next').NextConfig} */
const nextConfig = {
    webpack(config, {isServer}) {
        config.plugins.push(
            new CopyPlugin({
                patterns: [
                    {
                        from: "node_modules/@rdkit/rdkit/dist/RDKit_minimal.wasm",
                        to: "static/chunks"
                    }
                ]
            })
        );

        if (!isServer) {
            config.resolve.fallback = {
                fs: false
            };
        }

        return config;
    },


    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://backend:5000/:path*' // Proxy to Backend
            },
            // See https://lifescience.opensource.epam.com/indigo/service/index.html
            // For how to use it with a proxy redirect later
            {
                source: '/indigo/:path*',
                destination: 'http://indigo:8002/:path*' // Proxy to Indigo
            }
        ]
    }
}

module.exports = nextConfig
