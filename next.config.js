/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "data.iledefrance-mobilites.fr",
        port: "",
        pathname: "/**",
      },
    ],
  },
};

module.exports = nextConfig;
