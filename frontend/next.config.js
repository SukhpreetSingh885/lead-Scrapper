/** @type {import('next').NextConfig} */

function getBackendDestination() {
  let url = (
    process.env.INTERNAL_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://127.0.0.1:8001"
  ).trim();

  // Strip wrapping single or double quotes
  url = url.replace(/^["']|["']$/g, "").trim();

  // Strip trailing slashes
  url = url.replace(/\/+$/, "");

  // If protocol was omitted in Vercel environment variables, prepend https://
  if (!url.startsWith("http://") && !url.startsWith("https://") && !url.startsWith("/")) {
    url = `https://${url}`;
  }

  return `${url}/api/v1/:path*`;
}

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",

  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: getBackendDestination(),
      },
    ];
  },
};

module.exports = nextConfig;
