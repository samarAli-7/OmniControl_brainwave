import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // Use the dedicated v4 plugin

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})