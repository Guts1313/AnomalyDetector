import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import type { TabDef } from "./components/Tabs";
import Orb from "./components/Orb";
import Overview from "./tabs/Overview";
import Alerts from "./tabs/Alerts";
import ManualScoring from "./tabs/ManualScoring";
import Examples from "./tabs/Examples";
import About from "./tabs/About";
import { api } from "./api/client";
import type { Health } from "./api/types";
import { nowTimeAmsterdam } from "./lib/time";

const TABS: TabDef[] = [
  { id: "overview", label: "Overview" },
  { id: "alerts", label: "Alerts" },
  { id: "manual", label: "Manual scoring" },
  { id: "examples", label: "Request examples" },
  { id: "about", label: "About" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<string>(TABS[0].id);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    let alive = true;
    api.health()
      .then((h) => alive && setHealth(h))
      .catch(() => alive && setHealth(null));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <div className="orb-background" aria-hidden>
        <Orb
          hue={0}
          hoverIntensity={0.6}
          rotateOnHover
          forceHoverState={false}
          backgroundColor="#050608"
          pointerSource="window"
        />
      </div>
      <Navbar
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
      />
      <main className="app-main" id="main">
        <div className="container">
          {activeTab === "overview" && <Overview />}
          {activeTab === "alerts" && <Alerts />}
          {activeTab === "manual" && <ManualScoring />}
          {activeTab === "examples" && <Examples />}
          {activeTab === "about" && <About />}
        </div>
        <footer className="app-footer">
          <span>
            API: <code>{import.meta.env.VITE_API_URL ?? "/api"}</code>
          </span>
          <span>Refreshed {nowTimeAmsterdam()} (Amsterdam)</span>
        </footer>
      </main>
    </div>
  );
}
