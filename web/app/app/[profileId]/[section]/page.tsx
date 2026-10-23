import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AlertCenter } from "@/components/alert-center";
import { AlertRulesForm } from "@/components/alert-rules";
import { CardView } from "@/components/card-view";
import { ReceiptView } from "@/components/receipt";
import { RunMonitorButton } from "@/components/run-monitor";
import { RunResult } from "@/components/run-result";
import { StubPage } from "@/components/stub-page";
import { ButtonLink } from "@/components/ui";
import { extraScreens, sections } from "@/lib/screens";

async function Section({ params }: { params: PageProps<"/app/[profileId]/[section]">["params"] }) {
  const { profileId, section } = await params;
  const meta = sections.find((s) => s.slug === section) ?? extraScreens[section as keyof typeof extraScreens];
  if (!meta) notFound();
  if (section === "run") return <RunResult profileId={profileId} />;
  if (section === "receipt") return <ReceiptView profileId={profileId} />;
  if (section === "card") return <CardView profileId={profileId} />;
  if (section === "alerts") return <AlertCenter profileId={profileId} />;
  if (section === "settings") return <AlertRulesForm profileId={profileId} />;

  return (
    <StubPage title={meta.label} purpose={meta.purpose} screen={meta.screen}>
      {section === "dashboard" && (
        <>
          <RunMonitorButton profileId={profileId} />
          <ButtonLink href={`/app/${profileId}/run`} variant="secondary">Last run</ButtonLink>
          <ButtonLink href={`/app/${profileId}/card`} variant="secondary">Profile card</ButtonLink>
        </>
      )}
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
