import styles from './Card.module.css';

export default function Card({
  children,
  interactive = false,
  className = '',
  eyebrow,
  eyebrowRight,
  ...props
}) {
  return (
    <div
      className={`${styles.card} ${interactive ? styles.cardInteractive : ''} ${className}`}
      {...props}
    >
      {eyebrow && (
        <div className={styles.eyebrow}>
          <span>{eyebrow}</span>
          {eyebrowRight && <span>{eyebrowRight}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className={styles.cardHeader}>
      <div>
        <h3 className={styles.cardTitle}>{title}</h3>
        {subtitle && <p className={styles.cardSubtitle}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function CardBody({ children }) {
  return <div className={styles.cardBody}>{children}</div>;
}

export function MetricCard({ value, label, eyebrow, delta, unit }) {
  return (
    <div className={styles.metricCard}>
      {eyebrow && <div className={styles.metricEyebrow}>{eyebrow}</div>}
      <div className={styles.metricValue}>
        {value}
        {unit && <span className={styles.metricUnit}>{unit}</span>}
      </div>
      <div className={styles.metricLabel}>{label}</div>
      {delta && <div className={styles.metricDelta}>{delta}</div>}
    </div>
  );
}
