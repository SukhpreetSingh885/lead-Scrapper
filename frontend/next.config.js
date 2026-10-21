
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",

  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${
          process.env.INTERNAL_API_URL ||
          "http://127.0.0.1:8001"
        }/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
