interface RadialScoreProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
}

function getScoreColor(score: number): string {
  if (score >= 90) return '#34d399';
  if (score >= 75) return '#38bdf8';
  if (score >= 60) return '#fbbf24';
  if (score >= 40) return '#fb923c';
  return '#f87171';
}

function getGrade(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 75) return 'Good';
  if (score >= 60) return 'Fair';
  if (score >= 40) return 'Poor';
  return 'Critical';
}

export function RadialScore({
  score,
  maxScore = 100,
  size = 140,
  strokeWidth = 10,
  label,
  sublabel,
}: RadialScoreProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(score / maxScore, 1);
  const strokeDashoffset = circumference * (1 - pct);
  const color = getScoreColor(score);

  return (
    <div className="relative inline-flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-text-primary">{Math.round(score)}</span>
        <span className="text-xs text-text-muted">/ {maxScore}</span>
      </div>
      {(label || sublabel) && (
        <div className="mt-2 text-center">
          {label && <p className="text-sm font-medium text-text-primary">{label}</p>}
          {sublabel && <p className="text-xs text-text-secondary">{sublabel}</p>}
        </div>
      )}
    </div>
  );
}

interface GaugeScoreProps {
  score: number;
  size?: number;
  label?: string;
}

export function GaugeScore({ score, size = 200, label }: GaugeScoreProps) {
  const color = getScoreColor(score);
  const grade = getGrade(score);
  const r = (size - 24) / 2;
  const circumference = Math.PI * r;
  const pct = Math.min(score / 100, 1);
  const offset = circumference * (1 - pct);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 24} viewBox={`0 0 ${size} ${size / 2 + 24}`}>
        <path
          d={`M 12 ${size / 2 + 12} A ${r} ${r} 0 0 1 ${size - 12} ${size / 2 + 12}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d={`M 12 ${size / 2 + 12} A ${r} ${r} 0 0 1 ${size - 12} ${size / 2 + 12}`}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="text-center -mt-8">
        <p className="text-4xl font-bold" style={{ color }}>{Math.round(score)}</p>
        <p className="text-sm text-text-secondary mt-1">{grade}</p>
        {label && <p className="text-xs text-text-muted mt-1">{label}</p>}
      </div>
    </div>
  );
}
