import React from 'react';
import { Instagram, Facebook, Send, Coffee, Heart, ExternalLink } from 'lucide-react';

interface SocialBadgeProps {
    href: string;
    children: React.ReactNode;
    label: string;
    color: string;
}

const SocialBadge = ({ href, children, label, color, handle }: SocialBadgeProps & { handle?: string }) => (
    <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-border/50 transition-all duration-300 transform hover:scale-105 hover:shadow-lg ${color} text-muted-foreground group`}
        title={label}
    >
        {children}
        {handle && <span className="font-bold text-xs group-hover:text-current">{handle}</span>}
    </a>
);

interface SupportButtonProps {
    href: string;
    children: React.ReactNode;
    label: string;
    handle?: string;
    className: string;
}

const SupportButton = ({ href, children, label, handle, className }: SupportButtonProps) => (
    <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={`flex items-center gap-2 px-4 py-2 rounded-xl border font-bold text-xs uppercase tracking-wide transition-all duration-300 hover:shadow-md hover:-translate-y-0.5 ${className}`}
    >
        {children}
        <div className="flex flex-col leading-none">
            <span>{label}</span>
            {handle && <span className="text-[10px] opacity-80 normal-case tracking-normal">{handle}</span>}
        </div>
    </a>
);

export const SocialWatermark = () => {
    return (
        <div className="w-full mt-12 py-8 bg-gradient-to-r from-secondary/80 to-background border-t-2 border-primary/20 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-50" />

            <div className="max-w-[1600px] mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-8 items-center">

                {/* Left: Branding */}
                <div className="flex flex-col items-center md:items-start gap-2">
                    <h2 className="text-2xl font-black tracking-tighter text-foreground flex items-center gap-2">
                        <span className="text-primary">✦</span> CENAYANG MARKET
                    </h2>
                    <p className="text-sm font-medium text-muted-foreground tracking-wide">
                        Advanced Quant & Astro-Trading Analytics
                    </p>
                </div>

                {/* Center: Social Hub */}
                <div className="flex flex-wrap justify-center gap-3">
                    <SocialBadge href="https://x.com/CenayangMarket" label="Twitter / X" handle="@CenayangMarket" color="hover:border-white hover:text-white bg-black/20">
                        <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
                    </SocialBadge>
                    <SocialBadge href="https://www.instagram.com/cenayang.market" label="Instagram" handle="@cenayang.market" color="hover:border-pink-500 hover:text-pink-500 bg-pink-500/5">
                        <Instagram className="w-4 h-4" />
                    </SocialBadge>
                    <SocialBadge href="https://www.tiktok.com/@cenayang.market" label="TikTok" handle="@cenayang.market" color="hover:border-cyan-400 hover:text-cyan-400 bg-cyan-500/5">
                        <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" /></svg>
                    </SocialBadge>
                    <SocialBadge href="https://www.facebook.com/Cenayang.Market" label="Facebook" handle="Cenayang.Market" color="hover:border-blue-600 hover:text-blue-600 bg-blue-600/5">
                        <Facebook className="w-4 h-4" />
                    </SocialBadge>
                    <SocialBadge href="https://t.me/cenayangmarket" label="Telegram" handle="@cenayangmarket" color="hover:border-blue-400 hover:text-blue-400 bg-blue-400/5">
                        <Send className="w-4 h-4" />
                    </SocialBadge>
                </div>

                {/* Right: Support/Donation */}
                <div className="flex flex-wrap justify-center md:justify-end gap-3">
                    <SupportButton href="https://saweria.co/CenayangMarket" label="Saweria" handle="CenayangMarket" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20 hover:bg-yellow-500 hover:text-black">
                        <Coffee className="w-4 h-4" />
                    </SupportButton>
                    <SupportButton href="https://trakteer.id/Cenayang.Market/tip" label="Trakteer" handle="Cenayang.Market" className="bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white">
                        <Heart className="w-4 h-4" />
                    </SupportButton>
                    <SupportButton href="https://patreon.com/Cenayangmarket" label="Patreon" handle="Cenayangmarket" className="bg-orange-500/10 text-orange-500 border-orange-500/20 hover:bg-orange-500 hover:text-white">
                        <ExternalLink className="w-4 h-4" />
                    </SupportButton>
                </div>

            </div>
        </div>
    );
};
