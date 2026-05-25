import { AlertTriangle, CalendarDays, Columns3, Hash, Rows3, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

import type { DatasetProfile } from '../types/dataset';
import { formatPercent } from '../utils/format';
import { MetricCard } from './MetricCard';

interface ProfilePreviewProps {
  profile: DatasetProfile;
}

export function ProfilePreview({ profile }: ProfilePreviewProps) {
  const missingPercent = profile.rows * profile.columns
    ? (profile.total_missing_values / (profile.rows * profile.columns)) * 100
    : 0;

  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
      initial={{ opacity: 0, y: 16 }}
      transition={{ duration: 0.35 }}
    >
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm text-cyan">Dataset profile generated</p>
          <h2 className="mt-2 break-words text-3xl font-semibold text-white">{profile.filename}</h2>
        </div>
        <div className="rounded-lg border border-mint/25 bg-mint/10 px-4 py-3 text-sm text-mint">
          Ready for dynamic dashboards and AI analysis
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={Rows3} label="Rows" tone="cyan" value={profile.rows} />
        <MetricCard icon={Columns3} label="Columns" tone="mint" value={profile.columns} />
        <MetricCard icon={AlertTriangle} label="Missing" tone="amber" value={profile.total_missing_values} />
        <MetricCard icon={Hash} label="Duplicates" tone="coral" value={profile.duplicate_rows} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="glass rounded-lg p-5">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="text-cyan" size={18} />
            <h3 className="font-semibold text-white">Detected schema</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <SchemaGroup label="Numeric" values={profile.numeric_columns} />
            <SchemaGroup label="Categorical" values={profile.categorical_columns} />
            <SchemaGroup label="Dates" values={profile.date_columns} />
            <SchemaGroup label="Boolean" values={profile.boolean_columns} />
          </div>
        </div>

        <div className="glass rounded-lg p-5">
          <div className="mb-4 flex items-center gap-2">
            <CalendarDays className="text-amber" size={18} />
            <h3 className="font-semibold text-white">Quality snapshot</h3>
          </div>
          <div className="space-y-4 text-sm">
            <QualityRow label="Missing cell rate" value={formatPercent(missingPercent)} />
            <QualityRow label="Memory usage" value={`${profile.memory_usage_mb} MB`} />
            <QualityRow label="Profiled columns" value={profile.column_profiles.length} />
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="glass rounded-lg p-5">
          <h3 className="mb-4 font-semibold text-white">Chart recommendations</h3>
          <div className="space-y-3">
            {profile.chart_recommendations.map((chart) => (
              <div key={`${chart.chart_type}-${chart.title}`} className="rounded-lg border border-line bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-cyan/15 px-2 py-1 text-xs font-medium uppercase text-cyan">
                    {chart.chart_type}
                  </span>
                  <p className="font-medium text-white">{chart.title}</p>
                </div>
                <p className="mt-2 text-sm text-slate-400">{chart.reason}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="glass overflow-hidden rounded-lg">
          <div className="border-b border-line p-5">
            <h3 className="font-semibold text-white">Data preview</h3>
          </div>
          <div className="max-h-96 overflow-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="sticky top-0 bg-panel text-xs uppercase text-slate-400">
                <tr>
                  {Object.keys(profile.preview_rows[0] ?? {}).slice(0, 8).map((column) => (
                    <th className="whitespace-nowrap px-4 py-3 font-medium" key={column}>
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {profile.preview_rows.slice(0, 8).map((row, index) => (
                  <tr key={index} className="text-slate-300">
                    {Object.entries(row)
                      .slice(0, 8)
                      .map(([column, value]) => (
                        <td className="max-w-48 truncate px-4 py-3" key={column}>
                          {String(value ?? '-')}
                        </td>
                      ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.section>
  );
}

function SchemaGroup({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="rounded-lg border border-line bg-white/[0.03] p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {values.length ? (
          values.slice(0, 10).map((value) => (
            <span className="rounded-md bg-white/10 px-2 py-1 text-xs text-slate-200" key={value}>
              {value}
            </span>
          ))
        ) : (
          <span className="text-sm text-slate-500">None detected</span>
        )}
      </div>
    </div>
  );
}

function QualityRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-line bg-white/[0.03] px-4 py-3">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-white">{value}</span>
    </div>
  );
}
