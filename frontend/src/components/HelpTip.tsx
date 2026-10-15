import { useEffect, useRef, useState } from 'react'
import styles from './HelpTip.module.css'

interface HelpTipProps {
  label: string
  children: React.ReactNode
}

/**
 * Ayuda contextual accesible: botón (?) operable con mouse, clic, teclado y
 * tacto. El panel se cierra con Escape o al hacer clic fuera.
 */
export default function HelpTip({ label, children }: HelpTipProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!open) return
    function onPointer(event: MouseEvent | TouchEvent) {
      const target = event.target as Node
      if (containerRef.current && !containerRef.current.contains(target)) {
        setOpen(false)
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('touchstart', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('touchstart', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <span className={styles.container} ref={containerRef}>
      <button
        type="button"
        className={styles.trigger}
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden="true">?</span>
      </button>
      {open && (
        <span className={styles.popover} role="dialog" aria-label={label}>
          {children}
        </span>
      )}
    </span>
  )
}
