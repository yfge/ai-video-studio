"use client";

import { useEffect, useRef, type ReactNode } from "react";

export interface ModalProps {
  /**
   * Controls modal visibility
   */
  isOpen: boolean;
  /**
   * Callback when modal should close (ESC key or backdrop click)
   */
  onClose: () => void;
  /**
   * Optional modal title displayed in header
   */
  title?: string;
  /**
   * Modal content
   */
  children: ReactNode;
  /**
   * Optional footer content (action buttons, etc.)
   */
  footer?: ReactNode;
  /**
   * Max width class (default: 'max-w-2xl')
   */
  maxWidth?: string;
  /**
   * Disable backdrop click to close (default: false)
   */
  disableBackdropClick?: boolean;
  /**
   * Disable ESC key to close (default: false)
   */
  disableEscapeKey?: boolean;
  /**
   * Custom className for modal container
   */
  className?: string;
}

/**
 * Base Modal Component
 *
 * Reusable modal foundation with:
 * - Backdrop click to close
 * - ESC key support
 * - ARIA accessibility
 * - Customizable header/footer
 *
 * Usage:
 * ```tsx
 * <Modal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Edit User"
 *   footer={<Button onClick={handleSave}>Save</Button>}
 * >
 *   <form>...</form>
 * </Modal>
 * ```
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  maxWidth = "max-w-2xl",
  disableBackdropClick = false,
  disableEscapeKey = false,
  className = "",
}: ModalProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  // ESC key handler
  useEffect(() => {
    if (!isOpen || disableEscapeKey) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, disableEscapeKey, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disableBackdropClick) return;
    if (e.target === backdropRef.current) {
      onClose();
    }
  };

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      <div
        className={`bg-white rounded-lg shadow-xl ${maxWidth} w-full max-h-[90vh] flex flex-col ${className}`}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between p-6 border-b">
            <h2 id="modal-title" className="text-lg font-medium text-gray-900">
              {title}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
              aria-label="关闭对话框"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
