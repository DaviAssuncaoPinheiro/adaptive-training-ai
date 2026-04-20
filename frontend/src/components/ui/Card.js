import styles from './Card.module.css';

export default function Card({ children, interactive = false, className = '', ...props }) {
  return (
    <div
      className={`${styles.card} ${interactive ? styles.cardInteractive : ''} ${className}`}
      {...props}
    >
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

export function MetricCard({ value, label }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricValue}>{value}</div>
      <div className={styles.metricLabel}>{label}</div>
    </div>
  );
}
