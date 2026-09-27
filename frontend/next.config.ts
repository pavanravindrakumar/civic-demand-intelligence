import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for production Docker containers.
  // This produces a self-contained .next/standalone directory that includes
  // only the necessary server files (no node_modules copy required),
  // resulting in a smaller Docker image suitable for Cloud Run deployment.
  //
  // Production start command: node .next/standalone/server.js
  output: "standalone",
};

export default nextConfig;
