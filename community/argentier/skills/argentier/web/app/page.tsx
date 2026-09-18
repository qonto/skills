"use client";

import { useRouter } from "next/navigation";
import Landing from "./Landing";

export default function Page() {
  const router = useRouter();
  return <Landing onDemo={() => router.push("/demo")} />;
}
