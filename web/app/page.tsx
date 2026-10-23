import { OrbitHero } from "@/components/orbit-hero";
import { ButtonLink, Eyebrow, Logo, SampleBadge } from "@/components/ui";

const ledger = [
  ["Menu order changed", "Navigation"],
  ["Promo banner text replaced", "Promo banner"],
  ["CSS classes renamed, same text", "Formatting only"],
  ["Footer year updated", "Navigation"],
  ["Testimonials shuffled", "Reordering"],
];

const steps = [
  ["Describe your business", "One line or your website. We draft the profile and you correct it."],
  ["We find and watch competitors", "Companies serving India are found for you. Their public pricing and feature pages are checked politely."],
  ["Get proof, then a revised plan", "Real changes come with a dated receipt and update your launch scenarios. Redesign noise is listed, not alerted."],
];

export default function Landing() {
  return (
    <>
      <header className="sticky top-6 z-10 mx-4 sm:mx-auto sm:w-full sm:max-w-[1200px]">
        <nav className="flex items-center justify-between rounded-pill bg-white px-6 py-3 shadow-lift-1 sm:px-10">
          <Logo />
          <div className="flex items-center gap-3">
            <ButtonLink href="/login" variant="secondary" className="hidden sm:inline-flex">Log in</ButtonLink>
            <ButtonLink href="/app">Try the demo</ButtonLink>
          </div>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-[1200px] px-4 sm:px-12">
        <section className="grid items-center gap-12 py-16 md:grid-cols-[1.1fr_1fr] md:py-24">
          <div>
            <Eyebrow>Competitor monitoring for India</Eyebrow>
            <h1 className="mt-6 text-[40px] leading-[1] md:text-[64px]">Know when a competitor really changes.</h1>
            <p className="mt-6 max-w-[34rem] text-[18px] text-charcoal">
              RivalLens watches the public pricing and feature pages of companies competing with you in India. It ignores redesign noise, keeps a dated receipt for every real change, and shows what that change means for your own launch.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/app">Try the demo</ButtonLink>
              <ButtonLink href="/login" variant="secondary">Create an account</ButtonLink>
            </div>
          </div>
          <OrbitHero />
        </section>

        <section className="pb-24">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <h2 className="text-[28px] leading-tight md:text-[36px]">One monitoring run, explained</h2>
            <SampleBadge label="Example, fictional company" />
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="rounded-stadium bg-lifted p-8">
              <p className="text-[15px] text-slate">NimbusDeploy pricing page</p>
              <p className="mt-2 text-[24px] font-medium tracking-[-0.02em]">17 page changes · 15 ignored · 2 meaningful</p>
              <ul className="mt-6 divide-y divide-ink/10">
                {ledger.map(([what, why]) => (
                  <li key={what} className="flex justify-between gap-4 py-3 text-[15px]">
                    <span>{what}</span>
                    <span className="shrink-0 text-slate">Ignored: {why}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[14px] text-slate">and 10 more ignored changes, each with its reason</p>
            </div>
            <div className="rounded-stadium bg-white p-8 shadow-lift-2">
              <p className="inline-flex items-center gap-1.5 text-[14px] font-medium text-signal">
                <span className="size-1.5 rounded-full bg-signal" aria-hidden="true" />
                Meaningful change · price decrease
              </p>
              <p className="mt-3 text-[32px] font-medium tracking-[-0.02em]">Pro plan ₹1,499 → ₹899</p>
              <dl className="mt-4 grid grid-cols-2 gap-y-2 text-[14px]">
                <dt className="text-slate">Previously seen</dt>
                <dd>16 Oct 2026, 09:10 IST</dd>
                <dt className="text-slate">Change seen</dt>
                <dd>23 Oct 2026, 18:42 IST</dd>
              </dl>
              <div className="mt-6 grid gap-3 text-[14px] sm:grid-cols-2">
                <p className="rounded-btn bg-canvas p-4">
                  <span className="block text-slate">Before</span>
                  Pro <mark className="bg-ghost px-1">₹1,499 /month</mark> · 3 apps
                </p>
                <p className="rounded-btn bg-canvas p-4">
                  <span className="block text-slate">After</span>
                  Pro <mark className="bg-signal-light/25 px-1">₹899 /month</mark> · 3 apps
                </p>
              </div>
              <p className="mt-4 text-[13px] text-slate">Both versions of the page are saved, so the claim can be checked later.</p>
            </div>
          </div>
        </section>

        <section className="pb-24">
          <h2 className="text-[28px] leading-tight md:text-[36px]">How it works</h2>
          <ol className="mt-8 grid gap-6 md:grid-cols-3">
            {steps.map(([title, body], i) => (
              <li key={title} className="rounded-stadium border border-ink/15 p-8">
                <span className="flex size-10 items-center justify-center rounded-full border border-ink text-[15px]">{i + 1}</span>
                <h3 className="mt-6 text-[24px] leading-[1.2]">{title}</h3>
                <p className="mt-3 text-charcoal">{body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="mt-auto bg-ink px-4 py-16 text-white sm:px-12">
        <div className="mx-auto max-w-[1200px]">
          <p className="max-w-[40rem] text-[28px] font-medium leading-tight tracking-[-0.02em]">Public pages only. Every claim has a source and a date.</p>
          <p className="mt-6 text-[14px] text-dust">
            Built for HackNova&apos;26. Pages are checked only where robots.txt allows. Companies marked demo are fictional and their changes are simulated.
          </p>
        </div>
      </footer>
    </>
  );
}
