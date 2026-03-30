import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "VideoForge",
  description: "AI-Powered Video Creation Desktop Application - 从素材到成片，AI 全流程自动化",
  
  // GitHub Pages 部署路径
  base: '/VideoForge/',
  
  // 忽略死链接
  ignoreDeadLinks: true,
  
  srcDir: '.',
  
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/VideoForge/logo.png' }],
    ['meta', { name: 'theme-color', content: '#6366f1' }],
    ['meta', { name: 'og:type', content: 'website' }],
    ['meta', { name: 'og:title', content: 'VideoForge - AI 智能视频剪辑工具' }],
    ['meta', { name: 'og:description', content: '从素材到成片，AI 全流程自动化处理' }],
  ],

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    }
  },

  themeConfig: {
    logo: '/VideoForge/logo.png',
    siteTitle: 'VideoForge',

    nav: [
      { text: '🏠 首页', link: '/VideoForge/' },
      { text: '📖 指南', link: '/VideoForge/guide/getting-started' },
      { text: '🎯 功能', link: '/VideoForge/features' },
      { text: '🤖 AI 模型', link: '/VideoForge/ai-models' },
      { text: '⚙️ 配置', link: '/VideoForge/config' },
      { text: '❓ FAQ', link: '/VideoForge/faq' },
      {
        text: '🔗 更多',
        items: [
          { text: '📦 Changelog', link: '/VideoForge/changelog' },
          { text: '💻 GitHub', link: 'https://github.com/Agions/VideoForge' },
          { text: '🐛 Issues', link: 'https://github.com/Agions/VideoForge/issues' },
        ]
      }
    ],

    sidebar: {
      '/VideoForge/guide/': [
        {
          text: '📖 入门指南',
          items: [
            { text: '快速开始', link: '/VideoForge/guide/getting-started' },
            { text: '安装配置', link: '/VideoForge/guide/installation' },
            { text: '界面介绍', link: '/VideoForge/guide/interface' },
          ]
        },
        {
          text: '🎬 功能教程',
          items: [
            { text: 'AI 剧情分析', link: '/VideoForge/guide/ai-video-guide' },
            { text: 'AI 视频解说', link: '/VideoForge/guide/narration' },
            { text: 'AI 智能混剪', link: '/VideoForge/guide/mashup' },
          ]
        },
        {
          text: '⚙️ 高级配置',
          items: [
            { text: 'AI 模型配置', link: '/VideoForge/guide/ai-configuration' },
            { text: '快捷键', link: '/VideoForge/guide/shortcuts' },
          ]
        },
        {
          text: '🔧 故障排除',
          items: [
            { text: '常见问题', link: '/VideoForge/guide/troubleshooting' },
          ]
        },
      ],
      '/VideoForge/ai-models/': [
        {
          text: '🤖 AI 模型',
          items: [
            { text: '模型概览', link: '/VideoForge/ai-models' },
            { text: 'OpenAI', link: '/VideoForge/ai-models/openai' },
            { text: 'Anthropic Claude', link: '/VideoForge/ai-models/claude' },
            { text: 'Google Gemini', link: '/VideoForge/ai-models/gemini' },
            { text: '国产模型', link: '/VideoForge/ai-models/chinese' },
          ]
        }
      ],
      '/VideoForge/': [
        {
          text: '🎯 核心功能',
          items: [
            { text: '功能介绍', link: '/VideoForge/features' },
          ]
        },
        {
          text: '⚙️ 配置指南',
          items: [
            { text: '配置参考', link: '/VideoForge/config' },
          ]
        },
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/VideoForge' },
    ],

    footer: {
      message: '基于 MIT 许可证开源',
      copyright: 'Copyright © 2025-2026 Agions. All rights reserved.',
    },

    editLink: {
      pattern: 'https://github.com/Agions/VideoForge/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面'
    },

    search: {
      provider: 'local',
      options: {
        detailedView: true
      }
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    outline: {
      label: '页面导航',
      level: [2, 3]
    }
  }
})
