import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Upload, X } from 'lucide-react';

interface FileDropzoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(2)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}

export function FileDropzone({ file, onFileChange, disabled = false }: FileDropzoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (disabled) return;
      const dropped = e.dataTransfer.files[0];
      if (dropped && dropped.name.toLowerCase().endsWith('.csv')) {
        onFileChange(dropped);
      }
    },
    [disabled, onFileChange],
  );

  const handlePick = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const picked = e.target.files?.[0] ?? null;
      if (picked && picked.name.toLowerCase().endsWith('.csv')) {
        onFileChange(picked);
      }
      e.target.value = '';
    },
    [onFileChange],
  );

  if (file) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between gap-3 rounded-xl border border-accent-cyan/20 bg-accent-cyan/5 px-4 py-3"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 rounded-lg bg-accent-cyan/10 text-accent-cyan shrink-0">
            <FileText size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{file.name}</p>
            <p className="text-xs text-text-muted">{formatFileSize(file.size)} · CSV ready to analyze</p>
          </div>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={() => onFileChange(null)}
            className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors shrink-0"
            title="Remove file"
          >
            <X size={16} />
          </button>
        )}
      </motion.div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => {
        if (!disabled) document.getElementById('datasense-csv-drop')?.click();
      }}
      className={`
        rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200 group
        ${
          dragging
            ? 'border-accent-cyan bg-accent-cyan/10'
            : 'border-border-secondary bg-bg-card hover:border-accent-cyan/30 hover:bg-bg-card-hover'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}
      `}
    >
      <input
        id="datasense-csv-drop"
        type="file"
        accept=".csv"
        onChange={handlePick}
        className="hidden"
        disabled={disabled}
      />
      <div
        className={`
          p-4 rounded-xl w-fit mx-auto mb-4 transition-colors
          ${dragging ? 'bg-accent-cyan/20 text-accent-cyan' : 'bg-bg-glass text-text-muted group-hover:text-accent-cyan group-hover:bg-accent-cyan/10'}
        `}
      >
        <Upload size={28} />
      </div>
      <p className="text-text-primary font-medium">Drop your CSV here</p>
      <p className="text-sm text-text-muted mt-1">or browse files from your computer</p>
      <p className="text-xs text-text-muted mt-3">Accepts .csv files</p>
    </div>
  );
}