import styles from './Brand.module.css';

export function Mark({ size = 32, className = '' }) {
  return (
    <svg
      aria-hidden="true"
      className={`${styles.mark} ${className}`}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      focusable="false"
    >
      <g transform="translate(0 8)">
        <rect x="6" y="10" width="10" height="30" rx="1" />
        <rect x="48" y="10" width="10" height="30" rx="1" />
        <path d="M16 26 Q22 13 28 26 T40 26 T48 26" />
        <circle cx="22" cy="17" r="1.8" />
        <circle cx="40" cy="17" r="1.5" />
      </g>
    </svg>
  );
}

export default function Brand({ compact = false, className = '' }) {
  return (
    <span className={`${styles.brand} ${className}`}>
      <Mark size={compact ? 28 : 36} />
      {!compact && (
        <span className={styles.lockup}>
          <span className={styles.wordmark}>Adaptive</span>
          <span className={styles.tagline}>TRAINING · AI</span>
        </span>
      )}
    </span>
  );
}
