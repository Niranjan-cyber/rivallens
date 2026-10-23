import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AlertCenter } from "@/components/alert-center";
import { AlertRulesForm } from "@/components/alert-rules";
import { CardView } from "@/components/card-view";
import { ComparisonMatrix } from "@/components/comparison";
import { CompetitorDetail } from "@/components/competitor-detail";
import { Competitors } from "@/components/competitors";
import { Dashboard } from "@/components/dashboard";
import { Overview } from "@/components/overview";
import { ProductDetail } from "@/components/product-detail";
import { Products } from "@/components/products";
import { ReceiptView } from "@/components/receipt";
import { RunResult } from "@/components/run-result";
import { ReportView } from "@/components/report";
import { Simulator } from "@/components/simulator";
import { StubPage } from "@/components/stub-page";
import { extraScreens, sections } from "@/lib/screens";

async function Section({ params }: { params: PageProps<"/app/[profileId]/[section]">["params"] }) {
  const { profileId, section } = await params;
  const meta = sections.find((s) => s.slug === section) ?? extraScreens[section as keyof typeof extraScreens];
  if (!meta) notFound();
  if (section === "run") return <RunResult profileId={profileId} />;
  if (section === "receipt") return <ReceiptView profileId={profileId} />;
  if (section === "card") return <CardView profileId={profileId} />;
  if (section === "competitors") return <Competitors profileId={profileId} />;
  if (section === "competitor") return <CompetitorDetail profileId={profileId} />;
  if (section === "home") return <Overview profileId={profileId} />;
  if (section === "product") return <Products profileId={profileId} />;
  if (section === "product-detail") return <ProductDetail />;
  if (section === "dashboard") return <Dashboard profileId={profileId} />;
  if (section === "comparison") return <ComparisonMatrix profileId={profileId} />;
  if (section === "simulator") return <Simulator profileId={profileId} />;
  if (section === "reports") return <ReportView profileId={profileId} />;
  if (section === "alerts") return <AlertCenter profileId={profileId} />;
  if (section === "settings") return <AlertRulesForm profileId={profileId} />;

  return <StubPage title={meta.label} purpose={meta.purpose} screen={meta.screen} />;
}

export default function Page(props: PageProps<"/app/[profileId]/[section]">) {
  return (
    <Suspense fallback={<div className="h-40 rounded-stadium bg-lifted" />}>
      <Section params={props.params} />
    </Suspense>
  );
}
