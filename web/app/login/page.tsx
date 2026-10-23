import { ButtonLink, Logo, SampleBadge } from "@/components/ui";

export default function Login() {
  return (
    <main data-screen="S-02" className="mx-auto flex w-full max-w-[440px] flex-1 flex-col justify-center px-4 py-16">
      <Logo />
      <div className="mt-10 rounded-stadium bg-white p-8 shadow-lift-2">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-[28px] leading-tight">Log in</h1>
          <SampleBadge label="Coming next" />
        </div>
        <p className="mt-3 text-charcoal">Email sign-up and log-in arrive in the next build step. For now, explore the demo.</p>
        <ButtonLink href="/app" className="mt-6 w-full">Try the demo</ButtonLink>
      </div>
    </main>
  );
}
