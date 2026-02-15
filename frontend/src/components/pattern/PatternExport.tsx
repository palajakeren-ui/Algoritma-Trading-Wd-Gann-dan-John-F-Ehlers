import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Download,
  FileText,
  FileSpreadsheet,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { DetectedPattern, ManualAnalysis, AssetAnalysis } from "@/lib/patternUtils";
import { toast } from "@/hooks/use-toast";

interface PatternExportProps {
  patterns: DetectedPattern[];
  manualAnalyses: ManualAnalysis[];
  assets: AssetAnalysis[];
  instrument: string;
  timeframe: string;
}

export const PatternExport = ({
  patterns,
  manualAnalyses,
  assets,
  instrument,
  timeframe,
}: PatternExportProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState({
    patterns: true,
    manualAnalyses: true,
    assets: true,
    summary: true,
  });

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const generateCSV = () => {
    const rows: string[] = [];
    
    // Header
    rows.push("Pattern Recognition Export Report");
    rows.push(`Generated: ${formatDate(new Date())}`);
    rows.push(`Instrument: ${instrument}`);
    rows.push(`Timeframe: ${timeframe}`);
    rows.push("");

    // Patterns Section
    if (exportOptions.patterns && patterns.length > 0) {
      rows.push("=== DETECTED PATTERNS ===");
      rows.push("Name,Type,Signal,Confidence,Price Range,Time Window,Timeframe,Detected At");
      patterns.forEach((p) => {
        rows.push(
          `"${p.name}","${p.type}","${p.signal}",${(p.confidence * 100).toFixed(1)}%,"${p.priceRange}","${p.timeWindow}","${p.timeframe}","${formatDate(p.detectedAt)}"`
        );
      });
      rows.push("");
    }

    // Manual Analyses Section
    if (exportOptions.manualAnalyses && manualAnalyses.length > 0) {
      rows.push("=== MANUAL ANALYSES ===");
      rows.push("Instrument,Timeframe,Bias,Support,Resistance,Patterns,Notes,Created At");
      manualAnalyses.forEach((a) => {
        rows.push(
          `"${a.instrument}","${a.timeframe}","${a.bias}",${a.keyLevels.support},${a.keyLevels.resistance},"${a.patterns.join("; ")}","${a.notes}","${formatDate(a.createdAt)}"`
        );
      });
      rows.push("");
    }

    // Assets Section
    if (exportOptions.assets && assets.length > 0) {
      rows.push("=== TRACKED ASSETS ===");
      rows.push("Symbol,Name,Timeframes,Pattern Count,Last Updated");
      assets.forEach((a) => {
        rows.push(
          `"${a.symbol}","${a.name}","${a.timeframes.join("; ")}",${a.patternCount},"${formatDate(a.lastUpdated)}"`
        );
      });
      rows.push("");
    }

    // Summary Section
    if (exportOptions.summary) {
      rows.push("=== SUMMARY ===");
      const bullish = patterns.filter((p) => p.signal === "Bullish").length;
      const bearish = patterns.filter((p) => p.signal === "Bearish").length;
      const neutral = patterns.filter((p) => p.signal === "Neutral").length;
      const highConf = patterns.filter((p) => p.confidence >= 0.8).length;
      
      rows.push(`Total Patterns,${patterns.length}`);
      rows.push(`Bullish Signals,${bullish}`);
      rows.push(`Bearish Signals,${bearish}`);
      rows.push(`Neutral Signals,${neutral}`);
      rows.push(`High Confidence (≥80%),${highConf}`);
      rows.push(`Manual Analyses,${manualAnalyses.length}`);
      rows.push(`Tracked Assets,${assets.length}`);
    }

    return rows.join("\n");
  };

  const generatePDFContent = () => {
    let html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Pattern Recognition Report</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1a1a2e; background: #fff; }
    h1 { color: #2d3a4b; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }
    h2 { color: #3b82f6; margin-top: 30px; border-left: 4px solid #3b82f6; padding-left: 12px; }
    .meta { color: #64748b; margin-bottom: 20px; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }
    th { background: #3b82f6; color: white; padding: 12px 8px; text-align: left; }
    td { padding: 10px 8px; border-bottom: 1px solid #e2e8f0; }
    tr:nth-child(even) { background: #f8fafc; }
    .bullish { color: #10b981; font-weight: 600; }
    .bearish { color: #ef4444; font-weight: 600; }
    .neutral { color: #64748b; }
    .confidence { font-weight: bold; }
    .high { color: #10b981; }
    .medium { color: #f59e0b; }
    .low { color: #64748b; }
    .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
    .summary-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; }
    .summary-card .value { font-size: 28px; font-weight: bold; color: #2d3a4b; }
    .summary-card .label { font-size: 12px; color: #64748b; margin-top: 5px; }
    .footer { margin-top: 40px; text-align: center; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; padding-top: 20px; }
  </style>
</head>
<body>
  <h1>📊 Pattern Recognition Report</h1>
  <div class="meta">
    <p><strong>Instrument:</strong> ${instrument} | <strong>Timeframe:</strong> ${timeframe}</p>
    <p><strong>Generated:</strong> ${formatDate(new Date())}</p>
  </div>
`;

    // Summary
    if (exportOptions.summary) {
      const bullish = patterns.filter((p) => p.signal === "Bullish").length;
      const bearish = patterns.filter((p) => p.signal === "Bearish").length;
      const highConf = patterns.filter((p) => p.confidence >= 0.8).length;
      
      html += `
  <h2>📈 Summary</h2>
  <div class="summary-grid">
    <div class="summary-card">
      <div class="value">${patterns.length}</div>
      <div class="label">Total Patterns</div>
    </div>
    <div class="summary-card">
      <div class="value bullish">${bullish}</div>
      <div class="label">Bullish Signals</div>
    </div>
    <div class="summary-card">
      <div class="value bearish">${bearish}</div>
      <div class="label">Bearish Signals</div>
    </div>
    <div class="summary-card">
      <div class="value high">${highConf}</div>
      <div class="label">High Confidence</div>
    </div>
    <div class="summary-card">
      <div class="value">${manualAnalyses.length}</div>
      <div class="label">Manual Analyses</div>
    </div>
    <div class="summary-card">
      <div class="value">${assets.length}</div>
      <div class="label">Tracked Assets</div>
    </div>
  </div>
`;
    }

    // Patterns
    if (exportOptions.patterns && patterns.length > 0) {
      html += `
  <h2>🎯 Detected Patterns</h2>
  <table>
    <tr>
      <th>Pattern Name</th>
      <th>Type</th>
      <th>Signal</th>
      <th>Confidence</th>
      <th>Price Range</th>
      <th>Timeframe</th>
    </tr>
`;
      patterns.forEach((p) => {
        const confClass = p.confidence >= 0.85 ? "high" : p.confidence >= 0.7 ? "medium" : "low";
        html += `
    <tr>
      <td><strong>${p.name}</strong></td>
      <td>${p.type}</td>
      <td class="${p.signal.toLowerCase()}">${p.signal}</td>
      <td class="confidence ${confClass}">${(p.confidence * 100).toFixed(0)}%</td>
      <td>${p.priceRange}</td>
      <td>${p.timeframe}</td>
    </tr>
`;
      });
      html += `</table>`;
    }

    // Manual Analyses
    if (exportOptions.manualAnalyses && manualAnalyses.length > 0) {
      html += `
  <h2>📝 Manual Analyses</h2>
  <table>
    <tr>
      <th>Instrument</th>
      <th>Timeframe</th>
      <th>Bias</th>
      <th>Support</th>
      <th>Resistance</th>
      <th>Notes</th>
    </tr>
`;
      manualAnalyses.forEach((a) => {
        html += `
    <tr>
      <td>${a.instrument}</td>
      <td>${a.timeframe}</td>
      <td class="${a.bias.toLowerCase()}">${a.bias}</td>
      <td>${a.keyLevels.support.toLocaleString()}</td>
      <td>${a.keyLevels.resistance.toLocaleString()}</td>
      <td>${a.notes}</td>
    </tr>
`;
      });
      html += `</table>`;
    }

    // Assets
    if (exportOptions.assets && assets.length > 0) {
      html += `
  <h2>📊 Tracked Assets</h2>
  <table>
    <tr>
      <th>Symbol</th>
      <th>Name</th>
      <th>Timeframes</th>
      <th>Patterns</th>
      <th>Last Updated</th>
    </tr>
`;
      assets.forEach((a) => {
        html += `
    <tr>
      <td><strong>${a.symbol}</strong></td>
      <td>${a.name}</td>
      <td>${a.timeframes.join(", ")}</td>
      <td>${a.patternCount}</td>
      <td>${formatDate(a.lastUpdated)}</td>
    </tr>
`;
      });
      html += `</table>`;
    }

    html += `
  <div class="footer">
    Pattern Recognition Report • Generated by Trading Analysis Platform
  </div>
</body>
</html>
`;

    return html;
  };

  const downloadCSV = () => {
    const csv = generateCSV();
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `pattern_report_${instrument}_${timeframe}_${Date.now()}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast({
      title: "CSV Exported",
      description: `Pattern report exported successfully with ${patterns.length} patterns.`,
    });
  };

  const downloadPDF = () => {
    const htmlContent = generatePDFContent();
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
      }, 250);
    }
    
    toast({
      title: "PDF Export Ready",
      description: "Print dialog opened. Save as PDF for best results.",
    });
  };

  const totalItems =
    (exportOptions.patterns ? patterns.length : 0) +
    (exportOptions.manualAnalyses ? manualAnalyses.length : 0) +
    (exportOptions.assets ? assets.length : 0);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          Export Report
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Export Pattern Analysis
          </DialogTitle>
          <DialogDescription>
            Choose export format and sections to include in your report.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Export Options */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold">Include Sections</Label>
            <div className="space-y-2">
              {[
                { key: "patterns" as const, label: "Detected Patterns", count: patterns.length },
                { key: "manualAnalyses" as const, label: "Manual Analyses", count: manualAnalyses.length },
                { key: "assets" as const, label: "Tracked Assets", count: assets.length },
                { key: "summary" as const, label: "Summary Statistics", count: null },
              ].map((option) => (
                <div
                  key={option.key}
                  className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-3"
                >
                  <div className="flex items-center gap-3">
                    <Checkbox
                      checked={exportOptions[option.key]}
                      onCheckedChange={(checked) =>
                        setExportOptions((prev) => ({ ...prev, [option.key]: !!checked }))
                      }
                    />
                    <span className="text-sm font-medium">{option.label}</span>
                  </div>
                  {option.count !== null && (
                    <Badge variant="secondary" className="text-xs">
                      {option.count}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Preview Summary */}
          <Card className="bg-muted/30 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Items to export:</span>
              <span className="font-semibold text-foreground">{totalItems} items</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {patterns.length > 0 && (
                <>
                  <Badge className="bg-success/10 text-success border border-success/30 gap-1">
                    <TrendingUp className="h-3 w-3" />
                    {patterns.filter((p) => p.signal === "Bullish").length} Bullish
                  </Badge>
                  <Badge className="bg-destructive/10 text-destructive border border-destructive/30 gap-1">
                    <TrendingDown className="h-3 w-3" />
                    {patterns.filter((p) => p.signal === "Bearish").length} Bearish
                  </Badge>
                  <Badge className="bg-muted text-muted-foreground border border-border gap-1">
                    <Minus className="h-3 w-3" />
                    {patterns.filter((p) => p.signal === "Neutral").length} Neutral
                  </Badge>
                </>
              )}
            </div>
          </Card>

          {/* Export Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={downloadCSV}
              variant="outline"
              className="gap-2"
              disabled={totalItems === 0 && !exportOptions.summary}
            >
              <FileSpreadsheet className="h-4 w-4 text-success" />
              Export CSV
            </Button>
            <Button
              onClick={downloadPDF}
              className="gap-2 bg-gradient-to-r from-primary to-primary/80"
              disabled={totalItems === 0 && !exportOptions.summary}
            >
              <FileText className="h-4 w-4" />
              Export PDF
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
