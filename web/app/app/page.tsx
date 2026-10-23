import { ProfileList } from "@/components/profile-list";
import { ButtonLink } from "@/components/ui";

export default function Home() {
  return (
    <section data-screen="S-03">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Your businesses</h1>
      <p className="mt-3 text-[17px] text-charcoal">Pick a business to see its competitors, changes and launch scenarios.</p>
      <ProfileList />
      <ButtonLink href="/app/new" className="mt-8">Add a business</ButtonLink>
    </section>
  );
}
