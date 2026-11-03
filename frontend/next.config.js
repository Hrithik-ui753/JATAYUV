/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["three"],
  images: {
    domains: ["localhost", "127.0.0.1"],
    unoptimized: true,
  },
  webpack: (config) => {
    config.cache = false;
    return config;
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
      {
        source: "/storage/:path*",
        destination: "http://localhost:8000/storage/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
