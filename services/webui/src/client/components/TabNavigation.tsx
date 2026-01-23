import type { Tab } from '../types';

interface TabNavigationProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export default function TabNavigation({ tabs, activeTab, onChange }: TabNavigationProps) {
  return (
    <div className="flex gap-1 border-b border-ice-navy-700 mb-6">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-6 py-3 font-medium transition-colors duration-200 border-b-2 -mb-px ${
            activeTab === tab.id
              ? 'text-ice-gold-400 border-ice-gold-400'
              : 'text-ice-navy-400 border-transparent hover:text-ice-gold-400 hover:border-ice-navy-600'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
