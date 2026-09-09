import { type ReactNode } from 'react';
import { motion } from 'framer-motion';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export function Card({ children, className = '', hover = false, onClick }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
      className={`
        rounded-xl border border-border-primary bg-bg-card
        ${hover ? 'hover:bg-bg-card-hover hover:border-border-secondary cursor-pointer transition-colors duration-200' : ''}
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-5 py-4 border-b border-border-primary ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`p-5 ${className}`}>
      {children}
    </div>
  );
}
