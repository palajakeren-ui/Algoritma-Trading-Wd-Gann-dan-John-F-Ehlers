import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Bell, Send, Mail, MessageSquare, Phone, Smartphone, CheckCircle, XCircle, TestTube } from "lucide-react";
import { toast } from "sonner";

interface AlertChannel {
  id: string;
  name: string;
  icon: React.ReactNode;
  enabled: boolean;
  configured: boolean;
  config: Record<string, string>;
}

const AlertAPISettings = () => {
  const [channels, setChannels] = useState<AlertChannel[]>([
    {
      id: "telegram",
      name: "Telegram",
      icon: <Send className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { botToken: "", chatId: "" }
    },
    {
      id: "email",
      name: "Email",
      icon: <Mail className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { smtpServer: "", smtpPort: "587", email: "", password: "" }
    },
    {
      id: "sms",
      name: "SMS (Twilio)",
      icon: <Phone className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { accountSid: "", authToken: "", fromNumber: "", toNumber: "" }
    },
    {
      id: "discord",
      name: "Discord",
      icon: <MessageSquare className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { webhookUrl: "" }
    },
    {
      id: "slack",
      name: "Slack",
      icon: <MessageSquare className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { webhookUrl: "" }
    },
    {
      id: "pushover",
      name: "Pushover",
      icon: <Smartphone className="w-5 h-5" />,
      enabled: false,
      configured: false,
      config: { userKey: "", appToken: "" }
    },
  ]);

  const [alertTypes, setAlertTypes] = useState({
    priceAlert: true,
    gannSignal: true,
    ehlersSignal: true,
    aiPrediction: true,
    spikeDetection: true,
    positionUpdate: true,
    dailyReport: false,
  });

  const toggleChannel = (id: string) => {
    setChannels(prev => prev.map(ch => 
      ch.id === id ? { ...ch, enabled: !ch.enabled } : ch
    ));
  };

  const updateChannelConfig = (id: string, key: string, value: string) => {
    setChannels(prev => prev.map(ch => 
      ch.id === id ? { ...ch, config: { ...ch.config, [key]: value } } : ch
    ));
  };

  const testChannel = (channel: AlertChannel) => {
    toast.success(`Testing ${channel.name} connection...`);
    setTimeout(() => {
      const success = Math.random() > 0.3;
      if (success) {
        toast.success(`${channel.name} connected successfully!`);
        setChannels(prev => prev.map(ch => 
          ch.id === channel.id ? { ...ch, configured: true } : ch
        ));
      } else {
        toast.error(`Failed to connect to ${channel.name}. Check your credentials.`);
      }
    }, 1500);
  };

  const saveSettings = () => {
    toast.success("Alert API settings saved successfully!");
  };

  const renderChannelConfig = (channel: AlertChannel) => {
    switch (channel.id) {
      case "telegram":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Bot Token</Label>
              <Input
                type="password"
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                value={channel.config.botToken}
                onChange={(e) => updateChannelConfig(channel.id, "botToken", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Chat ID</Label>
              <Input
                placeholder="-1001234567890"
                value={channel.config.chatId}
                onChange={(e) => updateChannelConfig(channel.id, "chatId", e.target.value)}
              />
            </div>
          </div>
        );
      case "email":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <Label className="text-foreground text-sm">SMTP Server</Label>
              <Input
                placeholder="smtp.gmail.com"
                value={channel.config.smtpServer}
                onChange={(e) => updateChannelConfig(channel.id, "smtpServer", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">SMTP Port</Label>
              <Input
                placeholder="587"
                value={channel.config.smtpPort}
                onChange={(e) => updateChannelConfig(channel.id, "smtpPort", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Email Address</Label>
              <Input
                type="email"
                placeholder="your@email.com"
                value={channel.config.email}
                onChange={(e) => updateChannelConfig(channel.id, "email", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">App Password</Label>
              <Input
                type="password"
                placeholder="••••••••••••"
                value={channel.config.password}
                onChange={(e) => updateChannelConfig(channel.id, "password", e.target.value)}
              />
            </div>
          </div>
        );
      case "sms":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Account SID</Label>
              <Input
                type="password"
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={channel.config.accountSid}
                onChange={(e) => updateChannelConfig(channel.id, "accountSid", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Auth Token</Label>
              <Input
                type="password"
                placeholder="••••••••••••"
                value={channel.config.authToken}
                onChange={(e) => updateChannelConfig(channel.id, "authToken", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">From Number</Label>
              <Input
                placeholder="+1234567890"
                value={channel.config.fromNumber}
                onChange={(e) => updateChannelConfig(channel.id, "fromNumber", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">To Number</Label>
              <Input
                placeholder="+1234567890"
                value={channel.config.toNumber}
                onChange={(e) => updateChannelConfig(channel.id, "toNumber", e.target.value)}
              />
            </div>
          </div>
        );
      case "discord":
      case "slack":
        return (
          <div className="mt-4">
            <div className="space-y-2">
              <Label className="text-foreground text-sm">Webhook URL</Label>
              <Input
                type="password"
                placeholder={`https://hooks.${channel.id}.com/...`}
                value={channel.config.webhookUrl}
                onChange={(e) => updateChannelConfig(channel.id, "webhookUrl", e.target.value)}
              />
            </div>
          </div>
        );
      case "pushover":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <Label className="text-foreground text-sm">User Key</Label>
              <Input
                type="password"
                placeholder="uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={channel.config.userKey}
                onChange={(e) => updateChannelConfig(channel.id, "userKey", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-foreground text-sm">App Token</Label>
              <Input
                type="password"
                placeholder="axxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={channel.config.appToken}
                onChange={(e) => updateChannelConfig(channel.id, "appToken", e.target.value)}
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
          <Bell className="w-5 h-5 text-primary" />
          Alert API Configuration
        </h2>
        <Button onClick={saveSettings}>Save Settings</Button>
      </div>

      {/* Alert Types */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Alert Types</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(alertTypes).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
              <span className="text-sm text-foreground capitalize">
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              <Switch
                checked={value}
                onCheckedChange={(checked) => setAlertTypes(prev => ({ ...prev, [key]: checked }))}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Alert Channels */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">Alert Channels</h3>
        {channels.map((channel) => (
          <div 
            key={channel.id} 
            className="p-4 rounded-lg bg-secondary/30 border border-border"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  {channel.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-foreground">{channel.name}</h4>
                    {channel.configured ? (
                      <Badge className="bg-success/20 text-success border-0">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Connected
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">
                        <XCircle className="w-3 h-3 mr-1" />
                        Not Configured
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => testChannel(channel)}
                  disabled={!channel.enabled}
                >
                  <TestTube className="w-4 h-4 mr-2" />
                  Test
                </Button>
                <Switch
                  checked={channel.enabled}
                  onCheckedChange={() => toggleChannel(channel.id)}
                />
              </div>
            </div>
            
            {channel.enabled && renderChannelConfig(channel)}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default AlertAPISettings;
