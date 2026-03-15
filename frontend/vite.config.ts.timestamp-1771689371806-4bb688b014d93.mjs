// vite.config.ts
import { defineConfig } from "file:///C:/Users/ASUS/Downloads/New%20folder%20(3)/Test-feature-astro-risk-gui-scanner%20(hasilbaru)/gann_quant_ai/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/ASUS/Downloads/New%20folder%20(3)/Test-feature-astro-risk-gui-scanner%20(hasilbaru)/gann_quant_ai/frontend/node_modules/@vitejs/plugin-react-swc/index.js";
import path from "path";
import { componentTagger } from "file:///C:/Users/ASUS/Downloads/New%20folder%20(3)/Test-feature-astro-risk-gui-scanner%20(hasilbaru)/gann_quant_ai/frontend/node_modules/lovable-tagger/dist/index.js";
var __vite_injected_original_dirname = "C:\\Users\\ASUS\\Downloads\\New folder (3)\\Test-feature-astro-risk-gui-scanner (hasilbaru)\\gann_quant_ai\\frontend";
var vite_config_default = defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "./src")
    }
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor: React core
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          // Vendor: UI framework
          "vendor-ui": [
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-tabs",
            "@radix-ui/react-tooltip",
            "@radix-ui/react-slot",
            "@radix-ui/react-select",
            "@radix-ui/react-switch",
            "@radix-ui/react-progress",
            "@radix-ui/react-separator"
          ],
          // Vendor: Charting
          "vendor-charts": ["recharts"],
          // Vendor: Data & networking
          "vendor-data": [
            "@tanstack/react-query",
            "socket.io-client"
          ]
        }
      }
    }
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxBU1VTXFxcXERvd25sb2Fkc1xcXFxOZXcgZm9sZGVyICgzKVxcXFxUZXN0LWZlYXR1cmUtYXN0cm8tcmlzay1ndWktc2Nhbm5lciAoaGFzaWxiYXJ1KVxcXFxnYW5uX3F1YW50X2FpXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxBU1VTXFxcXERvd25sb2Fkc1xcXFxOZXcgZm9sZGVyICgzKVxcXFxUZXN0LWZlYXR1cmUtYXN0cm8tcmlzay1ndWktc2Nhbm5lciAoaGFzaWxiYXJ1KVxcXFxnYW5uX3F1YW50X2FpXFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9BU1VTL0Rvd25sb2Fkcy9OZXclMjBmb2xkZXIlMjAoMykvVGVzdC1mZWF0dXJlLWFzdHJvLXJpc2stZ3VpLXNjYW5uZXIlMjAoaGFzaWxiYXJ1KS9nYW5uX3F1YW50X2FpL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSBcInZpdGVcIjtcbmltcG9ydCByZWFjdCBmcm9tIFwiQHZpdGVqcy9wbHVnaW4tcmVhY3Qtc3djXCI7XG5pbXBvcnQgcGF0aCBmcm9tIFwicGF0aFwiO1xuaW1wb3J0IHsgY29tcG9uZW50VGFnZ2VyIH0gZnJvbSBcImxvdmFibGUtdGFnZ2VyXCI7XG5cbi8vIGh0dHBzOi8vdml0ZWpzLmRldi9jb25maWcvXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoKHsgbW9kZSB9KSA9PiAoe1xuICBzZXJ2ZXI6IHtcbiAgICBob3N0OiBcIjo6XCIsXG4gICAgcG9ydDogODA4MCxcbiAgfSxcbiAgcGx1Z2luczogW3JlYWN0KCksIG1vZGUgPT09IFwiZGV2ZWxvcG1lbnRcIiAmJiBjb21wb25lbnRUYWdnZXIoKV0uZmlsdGVyKEJvb2xlYW4pLFxuICByZXNvbHZlOiB7XG4gICAgYWxpYXM6IHtcbiAgICAgIFwiQFwiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vc3JjXCIpLFxuICAgIH0sXG4gIH0sXG4gIGJ1aWxkOiB7XG4gICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiA2MDAsXG4gICAgcm9sbHVwT3B0aW9uczoge1xuICAgICAgb3V0cHV0OiB7XG4gICAgICAgIG1hbnVhbENodW5rczoge1xuICAgICAgICAgIC8vIFZlbmRvcjogUmVhY3QgY29yZVxuICAgICAgICAgIFwidmVuZG9yLXJlYWN0XCI6IFtcInJlYWN0XCIsIFwicmVhY3QtZG9tXCIsIFwicmVhY3Qtcm91dGVyLWRvbVwiXSxcbiAgICAgICAgICAvLyBWZW5kb3I6IFVJIGZyYW1ld29ya1xuICAgICAgICAgIFwidmVuZG9yLXVpXCI6IFtcbiAgICAgICAgICAgIFwiQHJhZGl4LXVpL3JlYWN0LWRpYWxvZ1wiLFxuICAgICAgICAgICAgXCJAcmFkaXgtdWkvcmVhY3QtZHJvcGRvd24tbWVudVwiLFxuICAgICAgICAgICAgXCJAcmFkaXgtdWkvcmVhY3QtdGFic1wiLFxuICAgICAgICAgICAgXCJAcmFkaXgtdWkvcmVhY3QtdG9vbHRpcFwiLFxuICAgICAgICAgICAgXCJAcmFkaXgtdWkvcmVhY3Qtc2xvdFwiLFxuICAgICAgICAgICAgXCJAcmFkaXgtdWkvcmVhY3Qtc2VsZWN0XCIsXG4gICAgICAgICAgICBcIkByYWRpeC11aS9yZWFjdC1zd2l0Y2hcIixcbiAgICAgICAgICAgIFwiQHJhZGl4LXVpL3JlYWN0LXByb2dyZXNzXCIsXG4gICAgICAgICAgICBcIkByYWRpeC11aS9yZWFjdC1zZXBhcmF0b3JcIixcbiAgICAgICAgICBdLFxuICAgICAgICAgIC8vIFZlbmRvcjogQ2hhcnRpbmdcbiAgICAgICAgICBcInZlbmRvci1jaGFydHNcIjogW1wicmVjaGFydHNcIl0sXG4gICAgICAgICAgLy8gVmVuZG9yOiBEYXRhICYgbmV0d29ya2luZ1xuICAgICAgICAgIFwidmVuZG9yLWRhdGFcIjogW1xuICAgICAgICAgICAgXCJAdGFuc3RhY2svcmVhY3QtcXVlcnlcIixcbiAgICAgICAgICAgIFwic29ja2V0LmlvLWNsaWVudFwiLFxuICAgICAgICAgIF0sXG4gICAgICAgIH0sXG4gICAgICB9LFxuICAgIH0sXG4gIH0sXG59KSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQStnQixTQUFTLG9CQUFvQjtBQUM1aUIsT0FBTyxXQUFXO0FBQ2xCLE9BQU8sVUFBVTtBQUNqQixTQUFTLHVCQUF1QjtBQUhoQyxJQUFNLG1DQUFtQztBQU16QyxJQUFPLHNCQUFRLGFBQWEsQ0FBQyxFQUFFLEtBQUssT0FBTztBQUFBLEVBQ3pDLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxFQUNSO0FBQUEsRUFDQSxTQUFTLENBQUMsTUFBTSxHQUFHLFNBQVMsaUJBQWlCLGdCQUFnQixDQUFDLEVBQUUsT0FBTyxPQUFPO0FBQUEsRUFDOUUsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxLQUFLLFFBQVEsa0NBQVcsT0FBTztBQUFBLElBQ3RDO0FBQUEsRUFDRjtBQUFBLEVBQ0EsT0FBTztBQUFBLElBQ0wsdUJBQXVCO0FBQUEsSUFDdkIsZUFBZTtBQUFBLE1BQ2IsUUFBUTtBQUFBLFFBQ04sY0FBYztBQUFBO0FBQUEsVUFFWixnQkFBZ0IsQ0FBQyxTQUFTLGFBQWEsa0JBQWtCO0FBQUE7QUFBQSxVQUV6RCxhQUFhO0FBQUEsWUFDWDtBQUFBLFlBQ0E7QUFBQSxZQUNBO0FBQUEsWUFDQTtBQUFBLFlBQ0E7QUFBQSxZQUNBO0FBQUEsWUFDQTtBQUFBLFlBQ0E7QUFBQSxZQUNBO0FBQUEsVUFDRjtBQUFBO0FBQUEsVUFFQSxpQkFBaUIsQ0FBQyxVQUFVO0FBQUE7QUFBQSxVQUU1QixlQUFlO0FBQUEsWUFDYjtBQUFBLFlBQ0E7QUFBQSxVQUNGO0FBQUEsUUFDRjtBQUFBLE1BQ0Y7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLEVBQUU7IiwKICAibmFtZXMiOiBbXQp9Cg==
