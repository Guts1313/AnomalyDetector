export interface TabDef {
  id: string;
  label: string;
}

interface Props {
  tabs: TabDef[];
  activeTab: string;
  onTabChange: (id: string) => void;
}

export default function Tabs({ tabs, activeTab, onTabChange }: Props) {
  return (
    <nav className="tabs" role="tablist" aria-label="Sections">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={activeTab === t.id}
          className={`tab ${activeTab === t.id ? "active" : ""}`}
          onClick={() => onTabChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}
