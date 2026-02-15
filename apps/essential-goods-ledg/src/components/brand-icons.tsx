interface IconProps {
  size?: number
  className?: string
  weight?: 'thin' | 'regular' | 'bold'
}

const strokeWidths = {
  thin: 1.5,
  regular: 2,
  bold: 2.5
}

export function HeadstoneIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path 
        d="M 6 5 L 6 4 Q 6 3 7 3 L 17 3 Q 18 3 18 4 L 18 5 L 17 7 L 7 7 Z" 
        fill="currentColor" 
        opacity="0.1"
      />
      <path 
        d="M 6 7 L 6 20 Q 6 21 7 21 L 17 21 Q 18 21 18 20 L 18 7" 
        stroke="currentColor" 
        strokeWidth={sw} 
        fill="none"
        strokeLinejoin="round"
      />
      <line x1="8" y1="10" x2="16" y2="10" stroke="currentColor" strokeWidth={sw * 0.4} opacity="0.3" />
      <line x1="8" y1="13" x2="16" y2="13" stroke="currentColor" strokeWidth={sw * 0.4} opacity="0.3" />
      <path 
        d="M 9 16 L 10.5 13 L 12 15 L 13.5 12 L 15 14" 
        stroke="currentColor" 
        strokeWidth={sw * 0.8} 
        fill="none" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        opacity="0.6"
      />
      <circle cx="15.5" cy="18.5" r="1.2" fill="currentColor" opacity="0.4" />
      <line x1="6" y1="22" x2="18" y2="22" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function LedgerIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="4" y="4" width="16" height="16" rx="1" stroke="currentColor" strokeWidth={sw} />
      <line x1="4" y1="8" x2="20" y2="8" stroke="currentColor" strokeWidth={sw} />
      <line x1="4" y1="12" x2="20" y2="12" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
      <line x1="4" y1="16" x2="20" y2="16" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
      <line x1="10" y1="8" x2="10" y2="20" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
      <line x1="14" y1="8" x2="14" y2="20" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
      <circle cx="17" cy="17" r="1" fill="currentColor" />
    </svg>
  )
}

export function MintMarkIcon({ size = 24, className = "" }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="8" fill="currentColor" opacity="0.2" />
      <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="12" cy="12" r="1" fill="currentColor" />
    </svg>
  )
}

export function ArchivalStampIcon({ size = 24, className = "" }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2 2" opacity="0.6" />
      <circle cx="12" cy="12" r="7" stroke="currentColor" strokeWidth="2" fill="none" />
      <path d="m15 10-4 4-2-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path 
        d="M 12 3 L 12.5 2 M 12 21 L 12.5 22 M 3 12 L 2 12.5 M 21 12 L 22 12.5" 
        stroke="currentColor" 
        strokeWidth="1.5" 
        strokeLinecap="round"
        opacity="0.4"
      />
    </svg>
  )
}

export function DecayLineIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path 
        d="M 3 8 L 6 9 L 9 10 L 12 12 L 15 15 L 18 17 L 21 18" 
        stroke="currentColor" 
        strokeWidth={sw} 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <path 
        d="M 3 8 L 21 8" 
        stroke="currentColor" 
        strokeWidth={sw * 0.5} 
        strokeDasharray="2 2" 
        opacity="0.3"
      />
      <circle cx="3" cy="8" r="1.5" fill="currentColor" />
      <circle cx="21" cy="18" r="1.5" fill="currentColor" />
    </svg>
  )
}

export function FlatlineIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="3" cy="12" r="1.5" fill="currentColor" opacity="0.5" />
      <circle cx="9" cy="12" r="1" fill="currentColor" opacity="0.3" />
      <circle cx="15" cy="12" r="1" fill="currentColor" opacity="0.3" />
      <circle cx="21" cy="12" r="1.5" fill="currentColor" opacity="0.5" />
    </svg>
  )
}

export function GridPatternIcon({ size = 24, className = "" }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <line x1="6" y1="3" x2="6" y2="21" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <line x1="12" y1="3" x2="12" y2="21" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <line x1="18" y1="3" x2="18" y2="21" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <line x1="3" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <line x1="3" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
      <rect x="3" y="3" width="18" height="18" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <circle cx="18" cy="18" r="1.5" fill="currentColor" />
    </svg>
  )
}

export function EngravedLineIcon({ size = 24, className = "" }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <line x1="3" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="8" x2="21" y2="8" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="14" x2="21" y2="14" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="16" x2="21" y2="16" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="0.5" />
      <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

export function ForensicIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth={sw} />
      <path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <line x1="8" y1="11" x2="14" y2="11" stroke="currentColor" strokeWidth={sw * 0.6} opacity="0.5" />
      <line x1="8" y1="9" x2="14" y2="9" stroke="currentColor" strokeWidth={sw * 0.6} opacity="0.5" />
      <line x1="8" y1="13" x2="14" y2="13" stroke="currentColor" strokeWidth={sw * 0.6} opacity="0.5" />
      <circle cx="14" cy="9" r="0.8" fill="currentColor" />
    </svg>
  )
}

export function TruthIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path 
        d="M 12 3 L 4 7 L 4 11 C 4 16 12 21 12 21 C 12 21 20 16 20 11 L 20 7 L 12 3 Z" 
        stroke="currentColor" 
        strokeWidth={sw} 
        strokeLinejoin="round"
        fill="none"
      />
      <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <line x1="8" y1="9" x2="16" y2="9" stroke="currentColor" strokeWidth={sw * 0.4} opacity="0.3" />
    </svg>
  )
}

export function EvidenceIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="5" y="3" width="14" height="18" rx="1" stroke="currentColor" strokeWidth={sw} />
      <line x1="8" y1="7" x2="16" y2="7" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <line x1="8" y1="11" x2="16" y2="11" stroke="currentColor" strokeWidth={sw * 0.6} opacity="0.6" />
      <line x1="8" y1="14" x2="13" y2="14" stroke="currentColor" strokeWidth={sw * 0.6} opacity="0.6" />
      <circle cx="16" cy="17" r="2.5" stroke="currentColor" strokeWidth={sw} fill="none" />
      <line x1="17.8" y1="18.8" x2="20" y2="21" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function HourglassDecayIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path 
        d="M 8 3 L 16 3 L 16 8 L 12 12 L 16 16 L 16 21 L 8 21 L 8 16 L 12 12 L 8 8 L 8 3 Z" 
        stroke="currentColor" 
        strokeWidth={sw} 
        strokeLinejoin="round"
        fill="none"
      />
      <path 
        d="M 8 3 L 16 3" 
        stroke="currentColor" 
        strokeWidth={sw} 
        strokeLinecap="round"
      />
      <path 
        d="M 8 21 L 16 21" 
        stroke="currentColor" 
        strokeWidth={sw} 
        strokeLinecap="round"
      />
      <path 
        d="M 10 16 Q 10 17 12 17 Q 14 17 14 16 L 14 14 L 10 14 L 10 16" 
        fill="currentColor" 
        opacity="0.4"
      />
      <line x1="10" y1="18" x2="14" y2="18" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
    </svg>
  )
}

export function ArchiveBoxIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="4" y="4" width="16" height="4" stroke="currentColor" strokeWidth={sw} fill="none" />
      <path 
        d="M 4 8 L 4 19 Q 4 20 5 20 L 19 20 Q 20 20 20 19 L 20 8" 
        stroke="currentColor" 
        strokeWidth={sw} 
        fill="none"
      />
      <line x1="10" y1="13" x2="14" y2="13" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="m12 13 0 -2" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <line x1="7" y1="6" x2="17" y2="6" stroke="currentColor" strokeWidth={sw * 0.5} opacity="0.3" />
    </svg>
  )
}
