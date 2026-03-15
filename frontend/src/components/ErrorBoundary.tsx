import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface ErrorBoundaryProps {
    children: ReactNode;
    fallbackTitle?: string;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        this.setState({ errorInfo });
        console.error("[ErrorBoundary] Caught error:", error, errorInfo);
    }

    handleRetry = (): void => {
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    handleGoHome = (): void => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        window.location.href = "/";
    };

    render(): ReactNode {
        if (this.state.hasError) {
            return (
                <div className="flex items-center justify-center min-h-[400px] p-8">
                    <div className="max-w-lg w-full text-center space-y-6">
                        {/* Error Icon */}
                        <div className="mx-auto w-16 h-16 rounded-2xl bg-destructive/10 border border-destructive/20 flex items-center justify-center">
                            <AlertTriangle className="w-8 h-8 text-destructive" />
                        </div>

                        {/* Error Message */}
                        <div className="space-y-2">
                            <h2 className="text-xl font-bold text-foreground">
                                {this.props.fallbackTitle || "Something went wrong"}
                            </h2>
                            <p className="text-sm text-muted-foreground">
                                An unexpected error occurred while rendering this section.
                                You can try reloading the component or navigating home.
                            </p>
                        </div>

                        {/* Error Details (collapsible) */}
                        {this.state.error && (
                            <details className="text-left bg-secondary/30 rounded-lg border border-border p-4">
                                <summary className="text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
                                    Error Details
                                </summary>
                                <pre className="mt-3 text-xs text-destructive/80 overflow-x-auto whitespace-pre-wrap font-mono bg-black/20 rounded p-3">
                                    {this.state.error.message}
                                    {this.state.errorInfo?.componentStack && (
                                        <>
                                            {"\n\nComponent Stack:"}
                                            {this.state.errorInfo.componentStack}
                                        </>
                                    )}
                                </pre>
                            </details>
                        )}

                        {/* Action Buttons */}
                        <div className="flex items-center justify-center gap-3">
                            <button
                                onClick={this.handleRetry}
                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Try Again
                            </button>
                            <button
                                onClick={this.handleGoHome}
                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors border border-border"
                            >
                                <Home className="w-4 h-4" />
                                Go Home
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
