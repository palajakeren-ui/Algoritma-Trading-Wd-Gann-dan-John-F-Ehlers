import { Loader2 } from "lucide-react";

const PageLoader = () => (
    <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                <Loader2 className="w-7 h-7 text-primary animate-spin" />
            </div>
            <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Loading module...</p>
                <p className="text-xs text-muted-foreground">Initializing components</p>
            </div>
        </div>
    </div>
);

export default PageLoader;
