import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

/**
 * Blocking modal shown when the session expires *while a form has unsaved
 * changes*. Unlike the silent redirect of the no-unsaved-changes path, this
 * keeps the page (and the user's in-progress edits) mounted and warns them, so
 * nothing is lost without notice.
 *
 * It is deliberately *not* Escape-dismissable and traps focus: the user must
 * make a choice ("Sign in again" or "Dismiss"). "Dismiss" hides the modal but
 * keeps them on the expired page so they can still copy/save their edits; the
 * modal re-shows on the next 401.
 *
 * Mounted once at the app root, inside the auth + router context.
 */
const SessionExpiredModal: React.FC = () => {
  const {
    sessionExpiredBlocking,
    confirmSessionExpiredSignIn,
    dismissSessionExpiredBlocking,
  } = useAuth();
  const navigate = useNavigate();
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const signInButtonRef = useRef<HTMLButtonElement | null>(null);

  // Focus the primary action on open and trap Tab within the dialog. Escape is
  // intentionally swallowed (not dismissable) since this is a blocking choice.
  useEffect(() => {
    if (!sessionExpiredBlocking) return;
    signInButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        // Blocking: don't let Escape close it.
        event.preventDefault();
        return;
      }
      if (event.key !== "Tab") return;
      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusable = dialog.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [sessionExpiredBlocking]);

  if (!sessionExpiredBlocking) return null;

  const handleSignIn = () => {
    // Commit the deferred sign-out, then send the user to the login screen.
    confirmSessionExpiredSignIn();
    navigate("/login");
  };

  return (
    <div className="modal modal-open" data-testid="session-expired-modal">
      <div
        className="modal-box"
        role="dialog"
        aria-modal="true"
        aria-labelledby="session-expired-title"
        aria-describedby="session-expired-body"
        ref={dialogRef}
      >
        <h3
          id="session-expired-title"
          className="font-bold text-lg flex items-center gap-2 text-warning"
        >
          <AlertTriangle size={20} aria-hidden="true" />
          Session expired
        </h3>
        <p id="session-expired-body" className="py-4 text-sm">
          Your session has expired. Your unsaved changes are still here on this
          page. Copy anything you need, then sign in again.
        </p>
        <div className="modal-action">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={dismissSessionExpiredBlocking}
            data-testid="session-expired-dismiss"
          >
            Dismiss
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSignIn}
            ref={signInButtonRef}
            data-testid="session-expired-signin"
          >
            Sign in again
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionExpiredModal;
