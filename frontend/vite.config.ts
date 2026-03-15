import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// ============================================================================
// VITE CONFIG - Optimized for Zero Bottleneck
// ============================================================================

export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    // Enable HMR for fast development
    hmr: {
      overlay: true,
    },
  },
  
  plugins: [react()],
  
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  
  // Build optimizations
  build: {
    // Increase chunk warning limit
    chunkSizeWarningLimit: 600,
    
    // Minification
    minify: "esbuild",
    sourcemap: mode === "development",
    
    // Rollup optimizations for code splitting
    rollupOptions: {
      output: {
        // Manual chunks for optimal caching
        manualChunks: {
          // React core - rarely changes
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          
          // UI components - medium change frequency
          "vendor-ui": [
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-tabs",
            "@radix-ui/react-tooltip",
            "@radix-ui/react-slot",
            "@radix-ui/react-select",
            "@radix-ui/react-switch",
            "@radix-ui/react-progress",
            "@radix-ui/react-separator",
          ],
          
          // Charts - rarely changes
          "vendor-charts": ["recharts"],
          
          // Data fetching - rarely changes
          "vendor-data": [
            "@tanstack/react-query",
            "socket.io-client",
          ],
          
          // Icons - rarely changes
          "vendor-icons": ["lucide-react"],
          
          // Utilities - rarely changes
          "vendor-utils": [
            "clsx",
            "tailwind-merge",
            "class-variance-authority",
          ],
        },
        
        // Optimize chunk file names
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]",
      },
    },
    
    // Target modern browsers for smaller bundle
    target: "es2022",
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Disable brotli for faster builds (enable in production)
    reportCompressedSize: mode === "production",
  },
  
  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-router-dom",
      "recharts",
      "socket.io-client",
      "@tanstack/react-query",
    ],
    exclude: [],
  },
  
  // Enable ES build for faster dev builds
  esbuild: {
    logOverride: { "this-is-undefined-in-esm": "silent" },
  },
}));
