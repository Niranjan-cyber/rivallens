import Link from "next/link";
import { ButtonLink, SampleBadge } from "@/components/ui";
import { SAMPLE_PROFILE } from "@/lib/screens";

const profiles = [
  { name: "StackNest", kind: "Business · service", note: "Cloud deployment, Pune" },
  { name: "QuickKart", kind: "Business · service", note: "Quick commerce, Bengaluru" },
  { name: "Stride & Co.", kind: "Business · product", note: "Running shoes, D2C" },
  { name: "Qubit Labs", kind: "Idea", note: "Quantum computing access" },
];

export default function Home() {
  return (
    <section data-screen="S-03">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Your businesses</h1>
        <SampleBadge />
      </div>
      <p className="mt-3 text-[17px] text-charcoal">Pick a business to see its competitors, changes and launch scenarios.</p>
      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {profiles.map((p) => (
          <li key={p.name}>
            <Link href={`/app/${SAMPLE_PROFILE}/dashboard`} className="block rounded-stadium bg-lifted p-7 hover:shadow-lift-2">
              <p className="text-[14px] text-slate">{p.kind}</p>
              <p className="mt-1 text-[24px] font-medium tracking-[-0.02em]">{p.name} (demo)</p>
              <p className="mt-1 text-charcoal">{p.note}</p>
            </Link>
          </li>
        ))}
      </ul>
      <ButtonLink href="/app/new" className="mt-8">Add a business</ButtonLink>
    </section>
  );
}
