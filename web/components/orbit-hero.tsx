// The landing page's one memorable element: competitors orbiting your product,
// with one satellite carrying a real-looking change receipt.
const rivals = [
  { x: 92, y: 120, r: 34, label: "KiteHost" },
  { x: 404, y: 96, r: 40, label: "NimbusDeploy" },
  { x: 372, y: 392, r: 30, label: "Orbitly" },
];

export function OrbitHero() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[480px]" aria-label="Your business at the centre, three fictional competitors orbiting it">
      <svg viewBox="0 0 480 480" className="absolute inset-0 size-full" aria-hidden="true">
        <g className="orbit-drift">
          <path d="M60 250 C 70 120, 210 52, 330 74 S 470 210, 424 318" fill="none" stroke="var(--color-signal-light)" strokeWidth="1.3" />
          <path d="M424 318 C 380 430, 220 462, 128 396 S 38 300, 60 250" fill="none" stroke="var(--color-signal-light)" strokeWidth="1" strokeDasharray="2 6" />
        </g>
        <circle cx="240" cy="240" r="92" fill="var(--color-ink)" />
        <text x="240" y="232" textAnchor="middle" fill="var(--color-canvas)" fontSize="15" fontWeight="500">Your business</text>
        <text x="240" y="254" textAnchor="middle" fill="var(--color-dust)" fontSize="13">StackNest, Pune</text>
        {rivals.map((c) => (
          <g key={c.label}>
            <circle cx={c.x} cy={c.y} r={c.r} fill="var(--color-lifted)" stroke="var(--color-ink)" strokeWidth="1.2" />
            <text x={c.x} y={c.y + 4} textAnchor="middle" fontSize="12" fill="var(--color-charcoal)">{c.label}</text>
          </g>
        ))}
      </svg>
      <div className="absolute right-0 top-[30%] w-[210px] translate-x-2 rounded-stadium bg-white p-5 shadow-lift-2 sm:translate-x-6">
        <p className="text-[13px] text-slate">NimbusDeploy · Pro plan</p>
        <p className="mt-1 text-[22px] font-medium tracking-[-0.02em]">
          <span className="text-slate line-through decoration-1">₹1,499</span> → ₹899
        </p>
        <p className="mt-2 inline-flex items-center gap-1.5 text-[13px] font-medium text-signal">
          <span className="size-1.5 rounded-full bg-signal" aria-hidden="true" />
          Meaningful change, −40%
        </p>
        <p className="mt-1 text-[12px] text-slate">Seen 23 Oct 2026, 18:42 IST</p>
      </div>
    </div>
  );
}
