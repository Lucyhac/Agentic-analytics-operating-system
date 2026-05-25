import { ChangeEvent, DragEvent, useRef, useState } from 'react';
import { FileSpreadsheet, Loader2, UploadCloud } from 'lucide-react';
import { motion } from 'framer-motion';

const acceptedExtensions = ['.csv', '.xls', '.xlsx'];

interface UploadDropzoneProps {
  isUploading: boolean;
  progress: number;
  onFileSelected: (file: File) => void;
}

export function UploadDropzone({ isUploading, progress, onFileSelected }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file?: File) => {
    if (!file) return;
    onFileSelected(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files[0]);
  };

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
  };

  return (
    <motion.div
      animate={{ scale: isDragging ? 1.01 : 1 }}
      className={`glass aurora-panel rounded-lg border-dashed p-6 transition ${
        isDragging ? 'border-cyan bg-cyan/10' : 'border-line'
      }`}
      onDragLeave={() => setIsDragging(false)}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        accept={acceptedExtensions.join(',')}
        className="hidden"
        onChange={handleInput}
        type="file"
      />

      <div className="relative flex flex-col items-center py-9 text-center">
        <div className="mb-5 grid h-16 w-16 place-items-center rounded-lg bg-cyan/15 text-cyan shadow-glow">
          {isUploading ? <Loader2 className="animate-spin" size={30} /> : <UploadCloud size={30} />}
        </div>
        <h2 className="max-w-xl text-2xl font-semibold text-white">Upload a dataset to generate your AI dashboard</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
          Drop a CSV or Excel file here. The backend will profile columns, quality issues, statistics, KPI candidates,
          and chart recommendations automatically.
        </p>

        <button
          className="mt-7 inline-flex items-center gap-2 rounded-lg bg-cyan px-5 py-3 text-sm font-semibold text-ink shadow-glow transition hover:bg-cyan/90 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
          type="button"
        >
          <FileSpreadsheet size={18} />
          Choose File
        </button>

        <p className="mt-4 text-xs text-slate-500">Supported formats: CSV, XLS, XLSX</p>
      </div>

      {isUploading && (
        <div className="mt-3">
          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-cyan transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-2 text-right text-xs text-slate-400">{progress}% uploaded</p>
        </div>
      )}
    </motion.div>
  );
}
