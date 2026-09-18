import type { RiskLevel } from '../../types/analysis'

export interface RiskStyle {
  /** Human-facing label. */
  label: string
  /** Raw hex — for SVG/gauge fills and chart colours. */
  hex: string
  /** Tailwind utility fragments (kept whole so the JIT can see them). */
  text: string
  bg: string
  border: string
  dot: string
  ring: string
  /** Ready-made chip classes for badges. */
  pill: string
  /** Icon tile background for section headers. */
  tile: string
}

// Warm, ink-compatible risk tints: sage / ochre / terracotta / brick.
export const RISK_STYLES: Record<RiskLevel, RiskStyle> = {
  LOW: {
    label: 'LOW',
    hex: '#2f6b47',
    text: 'text-[#2f6b47]',
    bg: 'bg-[#f1f7f3]',
    border: 'border-[#cfe3d7]',
    dot: 'bg-[#2f6b47]',
    ring: 'ring-[#2f6b47]',
    pill: 'border-[#cfe3d7] bg-[#f1f7f3] text-[#2f6b47]',
    tile: 'bg-[#e3efe7] text-[#2f6b47]',
  },
  MEDIUM: {
    label: 'MEDIUM',
    hex: '#8a6212',
    text: 'text-[#8a6212]',
    bg: 'bg-[#fdf7ea]',
    border: 'border-[#ecdcb6]',
    dot: 'bg-[#8a6212]',
    ring: 'ring-[#8a6212]',
    pill: 'border-[#ecdcb6] bg-[#fdf7ea] text-[#8a6212]',
    tile: 'bg-[#f5e9cd] text-[#8a6212]',
  },
  HIGH: {
    label: 'HIGH',
    hex: '#a4461d',
    text: 'text-[#a4461d]',
    bg: 'bg-[#fdf2ec]',
    border: 'border-[#f0d5c6]',
    dot: 'bg-[#a4461d]',
    ring: 'ring-[#a4461d]',
    pill: 'border-[#f0d5c6] bg-[#fdf2ec] text-[#a4461d]',
    tile: 'bg-[#f7e2d6] text-[#a4461d]',
  },
  CRITICAL: {
    label: 'CRITICAL',
    hex: '#96231b',
    text: 'text-[#96231b]',
    bg: 'bg-[#fbeceb]',
    border: 'border-[#eecfcc]',
    dot: 'bg-[#96231b]',
    ring: 'ring-[#96231b]',
    pill: 'border-[#eecfcc] bg-[#fbeceb] text-[#96231b]',
    tile: 'bg-[#f6dcd9] text-[#96231b]',
  },
}

export const RISK_GUIDANCE: Record<RiskLevel, string> = {
  LOW: 'No significant issues detected.',
  MEDIUM: 'Review recommended.',
  HIGH: 'Manual review required.',
  CRITICAL: 'Manual review required before payment.',
}

export function riskStyle(level: RiskLevel | null | undefined) {
  return level ? RISK_STYLES[level] : RISK_STYLES.LOW
}

/** Upper bound (inclusive) of each band, used for the gauge legend. */
export const RISK_BANDS: { level: RiskLevel; from: number; to: number }[] = [
  { level: 'LOW', from: 0, to: 24 },
  { level: 'MEDIUM', from: 25, to: 49 },
  { level: 'HIGH', from: 50, to: 74 },
  { level: 'CRITICAL', from: 75, to: 100 },
]
