import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { logger } from '../utils/logger';

interface ErrorBoundaryProps {
    children: React.ReactNode;
    /** Optional custom fallback renderer. */
    fallback?: (error: Error, reset: () => void) => React.ReactNode;
}

interface ErrorBoundaryState {
    error: Error | null;
}

/**
 * Global error boundary. Catches render-time errors in the routed page tree so a
 * single broken component degrades to a branded fallback instead of a blank
 * white screen. Class component is required: error boundaries cannot be
 * expressed with hooks.
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { error };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        logger.error('ErrorBoundary caught a render error', error, info.componentStack);
    }

    reset = () => {
        this.setState({ error: null });
    };

    handleReload = () => {
        window.location.reload();
    };

    render() {
        const { error } = this.state;
        if (error) {
            if (this.props.fallback) {
                return this.props.fallback(error, this.reset);
            }
            return (
                <div
                    role="alert"
                    className="min-h-[50vh] flex items-center justify-center p-6"
                >
                    <div className="card bg-base-100 shadow-xl max-w-lg w-full border border-error/30">
                        <div className="card-body items-center text-center gap-4">
                            <div className="text-error">
                                <AlertTriangle size={48} aria-hidden="true" />
                            </div>
                            <h2 className="card-title text-2xl">Something went wrong</h2>
                            <p className="text-base-content/70">
                                The page hit an unexpected error and couldn&apos;t finish
                                rendering. Reloading usually clears it.
                            </p>
                            {error.message && (
                                <pre className="text-xs text-left bg-base-200 rounded-lg p-3 w-full overflow-x-auto whitespace-pre-wrap text-base-content/60">
                                    {error.message}
                                </pre>
                            )}
                            <div className="card-actions">
                                <button
                                    type="button"
                                    className="btn btn-primary"
                                    onClick={this.handleReload}
                                >
                                    Reload page
                                </button>
                                <button
                                    type="button"
                                    className="btn btn-ghost"
                                    onClick={this.reset}
                                >
                                    Try again
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
