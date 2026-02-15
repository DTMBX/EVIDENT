import { motion } from 'framer-motion'

interface LogoProps {
  className?: string
  size?: number
  animated?: boolean
  variant?: 'default' | 'monochrome' | 'inverted'
}

export function Logo({ className = "", size = 40, animated = false, variant = 'default' }: LogoProps) {
  if (animated) {
    return <AnimatedLogo className={className} size={size} variant={variant} />
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Chronos logo"
    >
      <path
        d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
        fill="currentColor"
        opacity="0.1"
      />
      
      <rect x="32" y="30" width="36" height="50" rx="2" fill="currentColor" opacity="0.08" />
      
      <path
        d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
      />
      
      <line x1="34" y1="35" x2="66" y2="35" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="49" x2="66" y2="49" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="63" x2="66" y2="63" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      
      <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      
      <path
        d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
      
      <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
      <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
      <circle cx="62" cy="78" r="1" fill="currentColor" />
      
      <line x1="30" y1="90" x2="70" y2="90" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

export function LogoIcon({ className = "", size = 40, variant = 'square' }: { className?: string; size?: number; variant?: 'square' | 'circle' }) {
  const content = (
    <>
      <path
        d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
        fill="currentColor"
        opacity="0.1"
      />
      
      <rect x="32" y="30" width="36" height="50" rx="2" fill="currentColor" opacity="0.08" />
      
      <path
        d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
      />
      
      <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      
      <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      
      <path
        d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
      
      <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
      <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
      <circle cx="62" cy="78" r="1" fill="currentColor" />
      
      <line x1="30" y1="90" x2="70" y2="90" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </>
  )

  if (variant === 'circle') {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="Chronos icon"
      >
        <circle cx="50" cy="50" r="48" fill="currentColor" opacity="0.05" />
        <circle cx="50" cy="50" r="48" stroke="currentColor" strokeWidth="1" opacity="0.2" />
        {content}
      </svg>
    )
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Chronos icon"
    >
      {content}
    </svg>
  )
}

export function LogoLockup({ className = "", height = 48 }: { className?: string; height?: number }) {
  return (
    <div className={`flex items-center gap-3 ${className}`} style={{ height }}>
      <LogoIcon size={height} />
      <span 
        className="font-mono font-bold tracking-tight"
        style={{ 
          fontSize: height * 0.45,
          lineHeight: 1,
          letterSpacing: '-0.02em'
        }}
      >
        CHRONOS
      </span>
    </div>
  )
}

function AnimatedLogo({ className = "", size = 40, variant = 'default' }: { className?: string; size?: number; variant?: 'default' | 'monochrome' | 'inverted' }) {
  const shouldReduceMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (shouldReduceMotion) {
    return (
      <motion.svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        aria-label="Chronos logo"
      >
        <path
          d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
          fill="currentColor"
          opacity="0.1"
        />
        <rect x="32" y="30" width="36" height="50" rx="2" fill="currentColor" opacity="0.08" />
        <path
          d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
          stroke="currentColor"
          strokeWidth="2.5"
          fill="none"
          strokeLinejoin="round"
        />
        <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
        <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
        <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
        <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
        <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
        <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
        <path
          d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.6"
        />
        <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
        <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
        <circle cx="62" cy="78" r="1" fill="currentColor" />
        <line x1="30" y1="90" x2="70" y2="90" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </motion.svg>
    )
  }

  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      aria-label="Chronos logo animated"
    >
      <motion.path
        d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
        fill="currentColor"
        opacity="0.1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      />
      
      <motion.rect
        x="32"
        y="30"
        width="36"
        height="50"
        rx="2"
        fill="currentColor"
        opacity="0.08"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.08 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      />
      
      <motion.path
        d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
      />
      
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 0.2 }} transition={{ duration: 0.3, delay: 0.6 }}>
        <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" />
        <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" />
        <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" />
        <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.75" />
        <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.75" />
        <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.75" />
      </motion.g>
      
      <motion.path
        d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.9, delay: 0.7, ease: "easeOut" }}
      />
      
      <motion.g
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4, delay: 1.4, type: "spring", stiffness: 180 }}
      >
        <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
        <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
        <circle cx="62" cy="78" r="1" fill="currentColor" />
      </motion.g>
      
      <motion.line
        x1="30"
        y1="90"
        x2="70"
        y2="90"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.5, delay: 1.1, ease: "easeOut" }}
      />
    </motion.svg>
  )
}

export function LogoSpinner({ className = "", size = 40 }: { className?: string; size?: number }) {
  const shouldReduceMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (shouldReduceMotion) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="Loading"
      >
        <LogoIcon size={size} />
      </svg>
    )
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Loading"
    >
      <motion.path
        d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
        fill="currentColor"
        opacity="0.1"
      />
      
      <motion.rect
        x="32"
        y="30"
        width="36"
        height="50"
        rx="2"
        fill="currentColor"
        opacity="0.08"
      />
      
      <path
        d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
      />
      
      <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      
      <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      
      <motion.path
        d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
        animate={{
          y: [-1, 1, -1]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.g
        animate={{
          opacity: [1, 0.6, 1]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1.5
        }}
      >
        <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
        <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
        <circle cx="62" cy="78" r="1" fill="currentColor" />
      </motion.g>
      
      <line x1="30" y1="90" x2="70" y2="90" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

export function LogoPulse({ className = "", size = 40 }: { className?: string; size?: number }) {
  const shouldReduceMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (shouldReduceMotion) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="Loading"
      >
        <LogoIcon size={size} />
      </svg>
    )
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Loading"
    >
      <motion.path
        d="M 30 20 L 30 15 Q 30 10 35 10 L 65 10 Q 70 10 70 15 L 70 20 L 65 30 L 35 30 Z"
        fill="currentColor"
        opacity="0.1"
        animate={{
          opacity: [0.1, 0.15, 0.1]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.rect
        x="32"
        y="30"
        width="36"
        height="50"
        rx="2"
        fill="currentColor"
        opacity="0.08"
        animate={{
          opacity: [0.08, 0.12, 0.08]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <path
        d="M 30 30 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 30"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
      />
      
      <line x1="34" y1="42" x2="66" y2="42" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="56" x2="66" y2="56" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      <line x1="34" y1="70" x2="66" y2="70" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      
      <line x1="40" y1="35" x2="40" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="50" y1="35" x2="50" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <line x1="60" y1="35" x2="60" y2="75" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      
      <motion.path
        d="M 38 60 L 42 52 L 46 56 L 50 48 L 54 50 L 58 45 L 62 50"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        animate={{
          opacity: [0.6, 0.8, 0.6]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.g
        animate={{
          scale: [1, 1.2, 1],
          opacity: [1, 0.7, 1]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <circle cx="62" cy="78" r="3.5" fill="currentColor" opacity="0.3" />
        <circle cx="62" cy="78" r="2.5" stroke="currentColor" strokeWidth="1" fill="none" />
        <circle cx="62" cy="78" r="1" fill="currentColor" />
      </motion.g>
      
      <line x1="30" y1="90" x2="70" y2="90" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}
