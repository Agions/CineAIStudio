import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "VideoForge",
  description: "AI-Powered Video Creation Desktop Application",
  ignoreDeadLinks: true,
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }]
  ],
  themeConfig: {
    logo: '/logo.png',
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'API', link: '/api/overview' },
      { text: 'Config', link: '/config' }
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Quick Start', link: '/guide/getting-started' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'AI Video Guide', link: '/guide/ai-video-guide' }
          ]
        },
        {
          text: 'Advanced',
          items: [
            { text: 'AI Configuration', link: '/guide/ai-configuration' },
            { text: 'Troubleshooting', link: '/guide/troubleshooting' }
          ]
        }
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Scene Analyzer', link: '/api/scene-analyzer' },
            { text: 'Script Generator', link: '/api/script-generator' },
            { text: 'Voice Generator', link: '/api/voice-generator' }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/VideoForge' }
    ],
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025-2026 Agions'
    },
    editLink: {
      pattern: 'https://github.com/Agions/VideoForge/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    }
  },
  vite: {
    server: {
      port: 5173
    }
  }
})
