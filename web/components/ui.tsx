import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 text-[17px] font-medium tracking-[-0.02em]">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
        <circle cx="11" cy="11" r="7.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
        <circle cx="18.2" cy="5.2" r="2.6" fill="var(--color-signal-light)" />
      </svg>
      RivalLens
    </Link>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="flex items-center gap-2 text-[14px] font-bold uppercase leading-none tracking-[0.04em]">
      <span className="size-1.5 rounded-full bg-signal-light" aria-hidden="true" />
      {children}
    </p>
  );
}

// A request that failed: say what, and let the founder try again (never an endless loading box or a fake empty state).
export function LoadError({ what, message, onRetry }: { what: string; message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="rounded-btn bg-lifted p-5 text-[15px]">
      <p className="font-medium">Couldn&apos;t load {what}.</p>
      <p className="mt-1 text-charcoal">{message}</p>
      <button type="button" onClick={onRetry} className="mt-3 rounded-btn border-[1.5px] border-ink bg-white px-4 py-1.5 font-medium">Try again</button>
    </div>
  );
}

export function SampleBadge({ label = "Sample data" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-pill border border-ink/40 bg-white px-3 py-1 text-[13px] text-charcoal">
      <span className="size-1.5 rounded-full bg-dust" aria-hidden="true" />
      {label}
    </span>
  );
}

const buttonStyles = {
  primary: "bg-ink text-canvas border-ink",
  secondary: "bg-white text-ink border-ink",
};

export function ButtonLink({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<typeof Link> & { variant?: keyof typeof buttonStyles }) {
  return (
    <Link
      {...props}
      className={`inline-flex min-h-11 items-center justify-center rounded-btn border-[1.5px] px-6 text-[16px] font-medium tracking-[-0.02em] active:translate-y-px ${buttonStyles[variant]} ${className}`}
    />
  );
}
