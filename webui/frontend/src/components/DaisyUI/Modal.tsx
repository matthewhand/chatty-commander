import React, { useEffect, useRef } from 'react';

export interface ModalAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
}

interface BaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  position?: 'center' | 'top' | 'bottom';
  closable?: boolean;
  className?: string;
}

interface ModalProps extends BaseModalProps {
  actions?: ModalAction[];
  showCloseButton?: boolean;
}

interface ConfirmModalProps extends Omit<BaseModalProps, 'children'> {
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: ModalAction['variant'];
  onConfirm: () => void;
  loading?: boolean;
}

const Modal: React.FC<ModalProps> = ({
  isOpen, onClose, title, children, actions = [],
  size = 'md', position = 'center', closable = true,
  showCloseButton = true, className = '',
}) => {
  const modalRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;
    if (typeof modal.showModal !== 'function' || typeof modal.close !== 'function') return;
    if (isOpen) { if (!modal.open) modal.showModal(); }
    else { if (modal.open) modal.close(); }
  }, [isOpen]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === modalRef.current && closable) onClose();
  };

  const getSizeClass = () => {
    const sizes = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-5xl', full: 'max-w-7xl h-full' };
    return `modal-box w-11/12 ${sizes[size] || sizes.md}`;
  };

  const getPositionClass = () => position === 'bottom' ? 'modal-bottom' : 'modal-middle';

  const getVariantClass = (variant?: ModalAction['variant']) => {
    const map = { primary: 'btn-primary', secondary: 'btn-secondary', success: 'btn-success', warning: 'btn-warning', error: 'btn-error', ghost: 'btn-ghost' };
    return map[variant || 'primary'];
  };

  return (
    <dialog ref={modalRef} className={`modal ${getPositionClass()} ${className}`} onClick={handleBackdropClick} aria-modal="true" aria-labelledby={title ? 'modal-dialog-title' : undefined} open={isOpen}>
      <div className={getSizeClass()} role="document">
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between mb-4">
            {title && <h3 id="modal-dialog-title" className="font-bold text-lg">{title}</h3>}
            {showCloseButton && closable && (
              <button className="btn btn-sm btn-circle btn-ghost" onClick={onClose} aria-label="Close modal">✕</button>
            )}
          </div>
        )}
        <div className="py-4">{isOpen && children}</div>
        {actions.length > 0 && (
          <div className="modal-action">
            {actions.map((action, index) => (
              <button key={index} className={`btn ${getVariantClass(action.variant)}`} onClick={action.onClick} disabled={action.disabled || action.loading}>
                {action.loading && <span className="loading loading-spinner" aria-hidden="true" />}
                {action.loading ? '' : action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </dialog>
  );
};

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen, onClose, onConfirm, title = 'Confirm Action', message,
  confirmText = 'Confirm', cancelText = 'Cancel', confirmVariant = 'primary', loading = false, ...props
}) => {
  const actions: ModalAction[] = [
    { label: cancelText, onClick: onClose, variant: 'ghost', disabled: loading },
    { label: confirmText, onClick: onConfirm, variant: confirmVariant, loading },
  ];
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} actions={actions} closable={!loading} {...props}>
      <div className="text-base-content"><p>{message}</p></div>
    </Modal>
  );
};

export const LoadingModal: React.FC<Omit<BaseModalProps, 'children'> & { message?: string }> = ({
  isOpen, onClose, title = 'Loading...', message = 'Please wait while we process your request.', ...props
}) => (
  <Modal isOpen={isOpen} onClose={onClose} title={title} closable={false} showCloseButton={false} {...props}>
    <div className="text-center py-8" role="status" aria-live="polite">
      <span className="loading loading-spinner loading-lg text-primary" aria-hidden="true" />
      <p className="mt-4 text-base-content/70">{message}</p>
    </div>
  </Modal>
);

export default Modal;
