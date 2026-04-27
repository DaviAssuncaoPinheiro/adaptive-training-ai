import styles from './Button.module.css';

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled = false,
  type = 'button',
  onClick,
  className = '',
  ...props
}) {
  const classNames = [
    styles.btn,
    styles[`btn-${variant}`],
    size !== 'md' && styles[`btn-${size}`],
    fullWidth && styles['btn-full'],
    loading && styles['btn-loading'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      className={classNames}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}
