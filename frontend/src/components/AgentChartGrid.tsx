import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Fragment } from 'react';

import type { AgentChart } from '../types/dataset';

interface AgentChartGridProps {
  charts: AgentChart[];
}

const colors = ['#67E8F9', '#6EE7B7', '#F6C85F', '#FF7A7A', '#A78BFA', '#F472B6'];

export function AgentChartGrid({ charts }: AgentChartGridProps) {
  if (!charts.length) return null;

  return (
    <section className="grid gap-6 xl:grid-cols-2">
      {charts.map((chart) => (
        <div className="glass rounded-lg p-5" key={`${chart.chart_type}-${chart.title}`}>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-cyan">{chart.chart_type}</p>
              <h3 className="mt-1 font-semibold text-white">{chart.title}</h3>
            </div>
          </div>
          <div className="h-72">
            {chart.chart_type === 'heatmap' ? (
              <Heatmap chart={chart} />
            ) : (
              <ResponsiveContainer height="100%" width="100%">
                {renderChart(chart)}
              </ResponsiveContainer>
            )}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-400">{chart.insight}</p>
        </div>
      ))}
    </section>
  );
}

function renderChart(chart: AgentChart) {
  if (chart.chart_type === 'pie') {
    return (
      <PieChart>
        <Pie data={chart.data} dataKey="value" innerRadius={58} nameKey="label" outerRadius={96} paddingAngle={2}>
          {chart.data.map((_, index) => (
            <Cell fill={colors[index % colors.length]} key={index} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ background: '#101623', border: '1px solid rgba(255,255,255,0.12)' }} />
      </PieChart>
    );
  }

  if (chart.chart_type === 'line') {
    return (
      <LineChart data={chart.data}>
        <CartesianGrid stroke="rgba(255,255,255,0.08)" />
        <XAxis dataKey="label" stroke="#94A3B8" tick={{ fontSize: 12 }} />
        <YAxis stroke="#94A3B8" tick={{ fontSize: 12 }} />
        <Tooltip contentStyle={{ background: '#101623', border: '1px solid rgba(255,255,255,0.12)' }} />
        <Line dataKey="value" dot={false} stroke="#67E8F9" strokeWidth={3} type="monotone" />
      </LineChart>
    );
  }

  if (chart.chart_type === 'scatter') {
    return (
      <ScatterChart>
        <CartesianGrid stroke="rgba(255,255,255,0.08)" />
        <XAxis dataKey={chart.x ?? undefined} name={chart.x ?? undefined} stroke="#94A3B8" tick={{ fontSize: 12 }} />
        <YAxis dataKey={chart.y ?? undefined} name={chart.y ?? undefined} stroke="#94A3B8" tick={{ fontSize: 12 }} />
        <Tooltip contentStyle={{ background: '#101623', border: '1px solid rgba(255,255,255,0.12)' }} />
        <Scatter data={chart.data} fill="#6EE7B7" />
      </ScatterChart>
    );
  }

  return (
    <BarChart data={chart.data}>
      <CartesianGrid stroke="rgba(255,255,255,0.08)" />
      <XAxis dataKey="label" stroke="#94A3B8" tick={{ fontSize: 12 }} />
      <YAxis stroke="#94A3B8" tick={{ fontSize: 12 }} />
      <Tooltip contentStyle={{ background: '#101623', border: '1px solid rgba(255,255,255,0.12)' }} />
      <Bar dataKey="value" fill="#67E8F9" radius={[6, 6, 0, 0]} />
    </BarChart>
  );
}

function Heatmap({ chart }: { chart: AgentChart }) {
  const xValues = Array.from(new Set(chart.data.map((item) => String(item.x))));
  const yValues = Array.from(new Set(chart.data.map((item) => String(item.y))));
  const values = new Map(chart.data.map((item) => [`${item.x}-${item.y}`, Number(item.value ?? 0)]));

  return (
    <div className="flex h-full flex-col gap-2 overflow-auto rounded-lg border border-line bg-ink/40 p-3">
      <div
        className="grid min-w-max gap-1"
        style={{ gridTemplateColumns: `90px repeat(${xValues.length}, minmax(56px, 1fr))` }}
      >
        <div />
        {xValues.map((x) => (
          <div className="truncate px-1 text-center text-[11px] text-slate-400" key={x}>
            {x}
          </div>
        ))}
        {yValues.map((y) => (
          <Fragment key={y}>
            <div className="truncate py-2 pr-2 text-right text-[11px] text-slate-400" key={`${y}-label`}>
              {y}
            </div>
            {xValues.map((x) => {
              const value = values.get(`${y}-${x}`) ?? 0;
              const intensity = Math.min(Math.abs(value), 1);
              const background = value >= 0
                ? `rgba(103, 232, 249, ${0.14 + intensity * 0.72})`
                : `rgba(255, 122, 122, ${0.14 + intensity * 0.72})`;
              return (
                <div
                  className="grid min-h-10 place-items-center rounded-md text-[11px] font-medium text-white"
                  key={`${y}-${x}`}
                  style={{ background }}
                  title={`${y} vs ${x}: ${value.toFixed(3)}`}
                >
                  {value.toFixed(2)}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </div>
  );
}
