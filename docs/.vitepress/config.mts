import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "VideoForge",
  description: "AI-Powered Video Creation Desktop Application",
  
  // GitHub Pages 路径前缀
  base: '/VideoForge/',
  
  // 忽略死链接
  ignoreDeadLinks: true,
  
  srcDir: '.',
  
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/logo.png' }],
    ['meta', { name: 'theme-color', content: '#6366f1' }],
  ],

  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'VideoForge',

    nav: [
      { text: '首页', link: '/VideoForge/' },
      { text: '指南', link: '/VideoForge/guide/getting-started' },
      { text: '功能', link: '/VideoForge/features' },
      { text: 'AI 模型', link: '/VideoForge/ai-models' },
      { text: 'FAQ', link: '/VideoForge/faq' },
      {
        text: 'GitHub',
        link: 'https://github.com/Agions/VideoForge'
      }
    ],

    sidebar: {
      '/VideoForge/guide/': [
        {
          text: '指南',
          items: [
            { text: '快速开始', link: '/VideoForge/guide/getting-started' },
            { text: '安装配置', link: '/VideoForge/guide/installation' },
          ]
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/VideoForge' },
    ],

    footer: {
      message: 'MIT License',
      copyright: 'Copyright © 2025-2026 Agions',
    },

    editLink: {
      pattern: 'https://github.com/Agions/VideoForge/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面'
    },

    search: {
      provider: 'local'
    }
  }
})
