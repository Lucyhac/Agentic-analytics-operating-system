import { useState } from 'react';
import { AlertCircle, Bot, Download, LineChart, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

import { AgentChartGrid } from './components/AgentChartGrid';
import { AgentConsole } from './components/AgentConsole';
import { ProfilePreview } from './components/ProfilePreview';
import { Sidebar } from './components/Sidebar';
import { UploadDropzone } from './components/UploadDropzone';
import { invokeAgent, uploadDataset } from './services/api';
import type { AgentChart, AgentResponse, DatasetProfile } from './types/dataset';

function App() {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [agentResponse, setAgentResponse] = useState<AgentResponse | null>(null);
  const [agentCharts, setAgentCharts] = useState<AgentChart[]>([]);

  const handleFileSelected = async (file: File) => {
    setError(null);
    setProgress(0);
    setIsUploading(true);

    try {
      const response = await uploadDataset(file, setProgress);
      setProfile(response.profile);
      setConversationId(null);
      setAgentResponse(null);
      setAgentCharts([]);
      setProgress(100);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Upload failed. Please try another file.';
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleAgentSubmit = async (message: string) => {
    if (!profile) return;
    setError(null);
    setIsAgentRunning(true);

    try {
      const response = await invokeAgent(profile.dataset_id, message, conversationId);
      setConversationId(response.conversation_id);
      setAgentResponse(response);
      setProfile(response.profile);
      if (response.charts.length) {
        setAgentCharts(response.charts);
      }
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Agent execution failed. Try a more specific request.';
      setError(message);
    } finally {
      setIsAgentRunning(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
          <header className="glass aurora-panel flex flex-col justify-between gap-5 rounded-lg px-5 py-6 lg:flex-row lg:items-center">
            <div className="relative">
              <p className="text-sm font-medium text-cyan">Agentic analytics operating system</p>
              <h1 className="mt-2 max-w-4xl text-3xl font-semibold leading-tight text-white md:text-5xl">
                Command your data agent. Watch the dashboard rebuild itself.
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-300 md:text-base">
                Upload a dataset, ask for cleaning, analysis, insights, or charts, and the agent executes safe tools
                while keeping the visual workspace in sync.
              </p>
            </div>
            <div className="relative grid grid-cols-3 gap-3 text-center text-xs text-slate-300">
              <Pill icon={ShieldCheck} label="Validated" />
              <Pill icon={LineChart} label="Dashboard" />
              <Pill icon={Bot} label="AI-ready" />
            </div>
          </header>

          <UploadDropzone isUploading={isUploading} onFileSelected={handleFileSelected} progress={progress} />

          {error && (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3 rounded-lg border border-coral/30 bg-coral/10 p-4 text-sm text-coral"
              initial={{ opacity: 0, y: 8 }}
            >
              <AlertCircle className="mt-0.5 shrink-0" size={18} />
              <span>{error}</span>
            </motion.div>
          )}

          {profile ? (
            <>
              <AgentConsole
                disabled={!profile}
                isRunning={isAgentRunning}
                lastResponse={agentResponse}
                onSubmit={handleAgentSubmit}
              />
              <AgentChartGrid charts={agentCharts} />
              <ProfilePreview profile={profile} />
            </>
          ) : (
            <section className="grid gap-4 md:grid-cols-3">
              <NextStep icon={LineChart} title="Auto dashboards" text="KPI cards and chart specs are generated from the dataset profile." />
              <NextStep icon={Bot} title="AI chat layer" text="Natural language requests will compile into approved Pandas operations." />
              <NextStep icon={Download} title="Exports" text="Cleaned files, chart snapshots, and PDF reports plug into this pipeline." />
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

function Pill({ icon: Icon, label }: { icon: typeof ShieldCheck; label: string }) {
  return (
    <div className="rounded-lg border border-line bg-white/[0.08] px-3 py-3 shadow-glow">
      <Icon className="mx-auto mb-2 text-cyan" size={18} />
      <span>{label}</span>
    </div>
  );
}

function NextStep({ icon: Icon, title, text }: { icon: typeof ShieldCheck; title: string; text: string }) {
  return (
    <div className="glass rounded-lg p-5">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-lg bg-white/10 text-cyan">
        <Icon size={19} />
      </div>
      <h3 className="font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
    </div>
  );
}

export default App;
