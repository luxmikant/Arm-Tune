"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const links = [
    { href: "/#problem", label: "Why it matters" },
    { href: "/#how", label: "How it works" },
    { href: "/#evidence", label: "Evidence" },
    { href: "/docs", label: "Docs", match: "/docs" },
  ];

  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="ArmTune Serve home">
        <span className="brand-mark">AT</span>
        <span>
          ArmTune <em>Serve</em>
        </span>
      </Link>
      <button
        className="menu-button"
        type="button"
        aria-expanded={open}
        aria-controls="main-nav"
        onClick={() => setOpen(!open)}
      >
        Menu
      </button>
      <nav id="main-nav" className={`main-nav${open ? " open" : ""}`}>
        {links.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            className={link.match && pathname.startsWith(link.match) ? "active" : ""}
            onClick={() => setOpen(false)}
          >
            {link.label}
          </Link>
        ))}
        <a
          className="nav-github"
          href="https://github.com/luxmikant/Arm-Tune"
          target="_blank"
          rel="noreferrer"
        >
          GitHub <span>↗</span>
        </a>
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer shell">
      <div className="footer-brand">
        <span className="brand-mark">AT</span>
        <span>ArmTune Serve</span>
      </div>
      <p>Arm64 LLM inference optimization, made observable.</p>
      <div className="footer-links">
        <Link href="/docs">Documentation</Link>
        <a href="https://github.com/luxmikant/Arm-Tune" target="_blank" rel="noreferrer">
          GitHub
        </a>
        <a
          href="https://huggingface.co/lshar/ARM-TUNE-CPU-INFERENCE-OPT"
          target="_blank"
          rel="noreferrer"
        >
          Hugging Face
        </a>
        <span>MIT License</span>
      </div>
      <small>
        © {new Date().getFullYear()} ArmTune Serve contributors
      </small>
    </footer>
  );
}
