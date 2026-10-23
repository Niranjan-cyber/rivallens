import { notFound } from "next/navigation";
import { Suspense } from "react";
import { StubPage } from "@/components/stub-page";
import { ButtonLink } from "@/components/ui";
import { extraScreens, sections } from "@/lib/screens";

async function Section({ params }: { params: PageProps<"/app/[profileId]/[section]">["params"] }) {
  const { profileId, section } = await params;
  const meta = sections.find((s) => s.slug === section) ?? extraScreens[section as keyof typeof extraScreens];
  if (!meta) notFound();

  return (
    <StubPage title={meta.label} purpose={meta.purpose} screen={meta.screen}>
      {section === "dashboard" && (
        <>
          <ButtonLink href={`/app/${profileId}/run`}>Run monitor</ButtonLink>
          <ButtonLink href={`/app/${profileId}/receipt`} variant="secondary">Open latest receipt</ButtonLink>
        </>
      )}
      {section === "run" && <ButtonLink href={`/app/${profileId}/receipt`}>Open receipt</ButtonLink>}
    </StubPage>
  );
}

export default function Page(props: PageProps<"/app/[profileId]/[section]">) {
  return (
    <Suspense fallback={<div className="h-40 rounded-stadium bg-lifted" />}>
      <Section params={props.params} />
    </Suspense>
  );
}
