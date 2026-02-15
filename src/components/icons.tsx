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

export function TimelineIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 12h18M3 12l3-3m-3 3l3 3" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="8" cy="12" r="2" fill="currentColor" />
      <circle cx="16" cy="12" r="2" fill="currentColor" />
      <path d="M8 8V6m8 2V6m-8 10v2m8-2v2" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function GenerationsIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M4 20v-8a4 4 0 0 1 4-4h0a4 4 0 0 1 4 4v8" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 20v-6a4 4 0 0 1 4-4h0a4 4 0 0 1 4 4v6" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" opacity="0.6" />
      <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth={sw} />
      <circle cx="16" cy="8" r="2" stroke="currentColor" strokeWidth={sw} opacity="0.6" />
    </svg>
  )
}

export function AffordabilityIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth={sw} />
      <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 2l2 2-2 2M8 20l-2 2 2 2" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" opacity="0.6" />
    </svg>
  )
}

export function VolatilityIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 12h3l2-4 4 8 3-6 2 4h4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 8h18M3 16h18" stroke="currentColor" strokeWidth={sw * 0.6} strokeLinecap="round" opacity="0.3" />
    </svg>
  )
}

export function BasketIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M4 10h16l-1.5 8a2 2 0 0 1-2 1.5H7.5a2 2 0 0 1-2-1.5L4 10z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M8 10V6a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="9" cy="14" r="1" fill="currentColor" />
      <circle cx="15" cy="14" r="1" fill="currentColor" />
    </svg>
  )
}

export function InsightIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M12 3a9 9 0 0 0-9 9c0 3.5 2 6.5 5 8v2h8v-2c3-1.5 5-4.5 5-8a9 9 0 0 0-9-9z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M9 18h6M12 8v4m0 2h.01" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function CompareIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="3" y="4" width="8" height="16" rx="1" stroke="currentColor" strokeWidth={sw} />
      <rect x="13" y="8" width="8" height="12" rx="1" stroke="currentColor" strokeWidth={sw} opacity="0.6" />
      <path d="M6 8h2m-2 4h2m-2 4h2M16 12h2m-2 4h2" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function DataSourceIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <ellipse cx="12" cy="6" rx="8" ry="3" stroke="currentColor" strokeWidth={sw} />
      <path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" stroke="currentColor" strokeWidth={sw} />
      <path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" stroke="currentColor" strokeWidth={sw} />
      <circle cx="17" cy="17" r="3" fill="currentColor" opacity="0.2" />
      <path d="M17 16v2m0 0l-1-1m1 1l1-1" stroke="currentColor" strokeWidth={sw * 0.8} strokeLinecap="round" />
    </svg>
  )
}

export function MethodologyIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" strokeWidth={sw} />
      <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="16" cy="16" r="1.5" fill="currentColor" />
    </svg>
  )
}

export function ExploreIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth={sw} />
      <path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M9 11h4m-2-2v4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function AnalyticsIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth={sw} />
      <path d="M7 14l3-3 3 3 4-4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="7" cy="14" r="1.5" fill="currentColor" />
      <circle cx="10" cy="11" r="1.5" fill="currentColor" />
      <circle cx="13" cy="14" r="1.5" fill="currentColor" />
      <circle cx="17" cy="10" r="1.5" fill="currentColor" />
    </svg>
  )
}

export function RefreshIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M21 12a9 9 0 1 1-3.5-7.1" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M21 5v7h-7" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function SettingsIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth={sw} />
      <path d="M12 3v2m0 14v2M3 12h2m14 0h2m-2.8-7.2 1.4-1.4M5.4 18.6l1.4-1.4m0-10.4L5.4 5.4m13.2 13.2-1.4-1.4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function ShareIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="18" cy="6" r="3" stroke="currentColor" strokeWidth={sw} />
      <circle cx="6" cy="12" r="3" stroke="currentColor" strokeWidth={sw} />
      <circle cx="18" cy="18" r="3" stroke="currentColor" strokeWidth={sw} />
      <path d="m8.5 13.5 7 3m0-9-7 3" stroke="currentColor" strokeWidth={sw} />
    </svg>
  )
}

export function HomeIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 10l9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M9 21v-7a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v7" stroke="currentColor" strokeWidth={sw} />
    </svg>
  )
}

export function TrendUpIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="m3 17 6-6 4 4 8-8" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 7h4v4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function TrendDownIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="m3 7 6 6 4-4 8 8" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 17h4v-4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function ClockIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth={sw} />
      <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function EducationIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M2 9l10-5 10 5-10 5L2 9z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M6 11.5v5.5a2 2 0 0 0 1 1.73l4 2.31a2 2 0 0 0 2 0l4-2.31a2 2 0 0 0 1-1.73v-5.5" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M22 10v6" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function DialogueIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M7 8h10M7 12h6" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
    </svg>
  )
}

export function WarningIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M12 9v4m0 4h.01" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
    </svg>
  )
}

export function VerifiedIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M12 2l2.5 5 5.5.8-4 3.9.9 5.3-4.9-2.6L7 17l.9-5.3-4-3.9 5.5-.8L12 2z" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function MonitoringIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" strokeWidth={sw} />
      <path d="M8 21h8M12 17v4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M6 8h12M6 11h8M6 14h6" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" opacity="0.6" />
      <circle cx="18" cy="8" r="1.5" fill="currentColor" />
      <path d="M7 8l3 3 3-3" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" opacity="0.4" />
    </svg>
  )
}

export function FilterIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M4 6h16M7 12h10M10 18h4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="4" cy="6" r="2" fill="currentColor" />
      <circle cx="20" cy="12" r="2" fill="currentColor" />
      <circle cx="14" cy="18" r="2" fill="currentColor" />
    </svg>
  )
}

export function ExportIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 10l5-5 5 5M12 5v12" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function CalendarIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth={sw} />
      <path d="M3 10h18M8 2v4m8-4v4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <rect x="7" y="14" width="2" height="2" rx=".5" fill="currentColor" />
      <rect x="11" y="14" width="2" height="2" rx=".5" fill="currentColor" />
      <rect x="15" y="14" width="2" height="2" rx=".5" fill="currentColor" />
    </svg>
  )
}

export function RemediationIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M12 2v4m0 12v4M2 12h4m12 0h4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth={sw} />
      <path d="M16.24 7.76l-1.41 1.41M9.17 14.83l-1.41 1.41M7.76 7.76l1.41 1.41M14.83 14.83l1.41 1.41" 
        stroke="currentColor" strokeWidth={sw} strokeLinecap="round" opacity="0.5" />
      <path d="M12 8a4 4 0 0 1 0 8" stroke="currentColor" strokeWidth={sw + 0.5} strokeLinecap="round" opacity="0.3" />
    </svg>
  )
}

export function TestIcon({ size = 24, className = "", weight = 'regular' }: IconProps) {
  const sw = strokeWidths[weight]
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M9 2v3m6-3v3" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <path d="M7 5h10a1 1 0 0 1 1 1v12a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V6a1 1 0 0 1 1-1z" 
        stroke="currentColor" strokeWidth={sw} strokeLinejoin="round" />
      <path d="M6 10h12" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" />
      <circle cx="10" cy="15" r="1.5" fill="currentColor" opacity="0.6" />
      <circle cx="14" cy="15" r="1.5" fill="currentColor" opacity="0.6" />
      <path d="M10 18h4" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" opacity="0.4" />
    </svg>
  )
}
