import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "VideoForge",
  description: "AI-Powered Video Creation Desktop Application - 从素材到成片，AI 全流程自动化",
  srcDir: '.',
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
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
    logo: '/logo.svg',
    siteTitle: 'VideoForge',

    nav: [
      { text: '🏠 首页', link: '/' },
      { text: '📖 指南', link: '/guide/getting-started' },
      { text: '🎯 功能', link: '/features' },
      { text: '🤖 AI 模型', link: '/ai-models' },
      { text: '⚙️ 配置', link: '/config' },
      { text: '❓ FAQ', link: '/faq' },
      {
        text: '🔗 更多',
        items: [
          { text: '📦 Changelog', link: '/changelog' },
          { text: '💻 GitHub', link: 'https://github.com/Agions/VideoForge' },
          { text: '🐛 Issues', link: 'https://github.com/Agions/VideoForge/issues' },
        ]
      }
    ],

    sidebar: {
      '/guide/': [
        {
          text: '📖 入门指南',
          items: [
            { text: '快速开始', link: '/guide/getting-started' },
            { text: '安装配置', link: '/guide/installation' },
            { text: '界面介绍', link: '/guide/interface' },
          ]
        },
        {
          text: '🎬 功能教程',
          items: [
            { text: 'AI 剧情分析', link: '/guide/ai-video-guide' },
            { text: 'AI 视频解说', link: '/guide/narration' },
            { text: 'AI 智能混剪', link: '/guide/mashup' },
          ]
        },
        {
          text: '⚙️ 高级配置',
          items: [
            { text: 'AI 模型配置', link: '/guide/ai-configuration' },
            { text: '快捷键', link: '/guide/shortcuts' },
          ]
        },
        {
          text: '🔧 故障排除',
          items: [
            { text: '常见问题', link: '/guide/troubleshooting' },
          ]
        },
      ],
      '/ai-models': [
        {
          text: '🤖 AI 模型',
          items: [
            { text: '模型概览', link: '/ai-models' },
            { text: 'OpenAI', link: '/ai-models/openai' },
            { text: 'Anthropic Claude', link: '/ai-models/claude' },
            { text: 'Google Gemini', link: '/ai-models/gemini' },
            { text: '国产模型', link: '/ai-models/chinese' },
          ]
        }
      ],
      '/': [
        {
          text: '🎯 核心功能',
          items: [
            { text: '功能介绍', link: '/features' },
          ]
        },
        {
          text: '⚙️ 配置指南',
          items: [
            { text: '配置参考', link: '/config' },
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
    },

    callouts: [
      {
        type: 'info',
        icon: '🚀',
        title: '新功能',
        color: '#6366f1'
      },
      {
        type: 'warning',
        icon: '⚠️',
        title: '注意',
        color: '#f59e0b'
      },
      {
        type: 'danger',
        icon: '🚨',
        title: '危险',
        color: '#ef4444'
      }
    ]
  }
})
