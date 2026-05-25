import { BarChart3, Bot, Database, Home, UploadCloud } from 'lucide-react';

const items = [
  { label: 'Overview', icon: Home, active: true },
  { label: 'Upload', icon: UploadCloud, active: true },
  { label: 'Dashboard', icon: BarChart3, active: false },
  { label: 'AI Analyst', icon: Bot, active: false },
  { label: 'Datasets', icon: Database, active: false },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 border-r border-line bg-ink/70 px-5 py-6 lg:block">
      <div className="mb-10 flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-cyan/15 text-cyan">
          <BarChart3 size={22} />
        </div>
        <div>
          <p className="text-base font-semibold">InsightForge</p>
          <p className="text-xs text-slate-400">AI analytics workspace</p>
        </div>
      </div>

      <nav className="space-y-2">
        {items.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left text-sm transition ${
              active ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'
            }`}
            type="button"
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
