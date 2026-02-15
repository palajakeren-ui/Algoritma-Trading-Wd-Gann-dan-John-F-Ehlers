import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PageSectionProps {
    title: string;
    icon?: React.ReactNode;
    children: React.ReactNode;
    defaultOpen?: boolean;
    className?: string;
    headerAction?: React.ReactNode;
}

export const PageSection = ({
    title,
    icon,
    children,
    defaultOpen = true,
    className,
    headerAction
}: PageSectionProps) => {
    const [isOpen, setIsOpen] = React.useState(defaultOpen);

    return (
        <Collapsible
            open={isOpen}
            onOpenChange={setIsOpen}
            className={cn("w-full transition-all duration-300", className)}
        >
            <Card className="overflow-hidden border-border bg-card/50 backdrop-blur-sm shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="p-4 md:p-6 pb-2 select-none group">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <CollapsibleTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-primary/10 hover:text-primary transition-colors">
                                    {isOpen ? (
                                        <ChevronUp className="h-5 w-5 animate-in fade-in zoom-in duration-300" />
                                    ) : (
                                        <ChevronDown className="h-5 w-5 animate-in fade-in zoom-in duration-300" />
                                    )}
                                </Button>
                            </CollapsibleTrigger>
                            <div className="flex items-center gap-2">
                                {icon && <div className="text-primary animate-pulse-slow">{icon}</div>}
                                <CardTitle className="text-lg md:text-xl font-bold tracking-tight group-hover:text-primary transition-colors cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
                                    {title}
                                </CardTitle>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {headerAction}
                            <div className={cn(
                                "h-2 w-2 rounded-full",
                                isOpen ? "bg-success animate-pulse" : "bg-muted"
                            )} />
                        </div>
                    </div>
                </CardHeader>
                <CollapsibleContent className="transition-all duration-500 ease-in-out data-[state=closed]:animate-collapse-up data-[state=open]:animate-collapse-down">
                    <CardContent className="p-4 md:p-6 pt-2">
                        <div className="border-t border-border/50 pt-4 mt-2">
                            {children}
                        </div>
                    </CardContent>
                </CollapsibleContent>
            </Card>
        </Collapsible>
    );
};
