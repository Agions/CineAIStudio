import { defineConfig } from 'vitepress'

export default defineConfig({
  cleanUrls: false,
  title: 'Narrafiilm',
  description: 'AI 驱动的专业视频创作桌面应用',
  base: '/Narrafiilm/',
  lang: 'en-US',
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/logo.png' }],
  ],

  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'Narrafiilm',

    nav: [
      { text: '首页', link: '/' },
      { text: '功能', link: '/features' },
      { text: '快速开始', link: '/guide/quick-start' },
      { text: '安装配置', link: '/guide/installation' },
      { text: 'AI 模型', link: '/ai-models' },
      { text: '导出', link: '/guide/exporting' },
      { text: 'FAQ', link: '/faq' },
      {
        text: '更多',
        items: [
          { text: '疑难排查', link: '/guide/troubleshooting' },
          { text: '架构', link: '/architecture' },
          { text: '安全', link: '/security' },
          { text: '贡献', link: '/contributing' },
        ],
      },
      {
        text: 'GitHub',
        link: 'https://github.com/Agions/Narrafiilm',
      },
    ],

    sidebar: {
      '/': [
        {
          text: '入门',
          items: [
            { text: '快速开始', link: '/guide/quick-start' },
            { text: '完整安装指南', link: '/guide/installation' },
          ],
        },
        {
          text: '功能',
          items: [
            { text: '功能介绍', link: '/features' },
            { text: '导出指南', link: '/guide/exporting' },
          ],
        },
        {
          text: '配置',
          items: [
            { text: 'AI 模型', link: '/ai-models' },
            { text: '疑难排查', link: '/guide/troubleshooting' },
          ],
        },
        {
          text: '参考',
          items: [
            { text: '架构', link: '/architecture' },
            { text: '安全', link: '/security' },
            { text: '贡献', link: '/contributing' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/Narrafiilm' },
    ],

    footer: {
      message: 'MIT License',
      copyright: 'Copyright © 2025-2026 Agions.',
    },
  },
})
