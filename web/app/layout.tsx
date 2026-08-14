import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://armtune.vercel.app"),
  title: "ArmTune Serve | Tune every token",
  description:
    "ArmTune Serve measures and recommends efficient LLM inference configurations for Arm64 cloud CPUs. Arm Performix-powered evidence, quality-gated recommendations.",
  openGraph: {
    title: "ArmTune Serve | Tune every token",
    description:
      "Arm64-aware LLM inference optimization. Measure quantization, threads and concurrency on your exact Arm hardware, then deploy the recommended configuration.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ArmTune Serve | Tune every token",
    description:
      "Arm64-aware LLM inference optimization with Arm Performix evidence.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
