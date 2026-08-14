/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    // Windows filesystems (exFAT/VHDX/OneDrive-backed drives) can return
    // EISDIR from fs.readlink on regular files. Avoid symlink resolution and
    // the filesystem cache snapshotter that triggers the same readlink path.
    config.resolve.symlinks = false;
    config.cache = false;
    return config;
  },
};

export default nextConfig;
