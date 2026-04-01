import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'VideoForge',
  description: 'AI 驱动的专业视频创作桌面应用',
  base: '/VideoForge/',
  lang: 'en-US',
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/VideoForge/logo.png' }],
  ],

  themeConfig: {
    logo: '/VideoForge/logo.png',
    siteTitle: 'VideoForge',

    nav: [
      { text: '首页', link: '/' },
      { text: '功能', link: '/features' },
      { text: 'AI 模型', link: '/ai-models' },
      { text: 'FAQ', link: '/faq' },
      { text: '架构', link: '/architecture' },
      { text: '安全', link: '/security' },
      { text: '贡献', link: '/contributing' },
      {
        text: 'GitHub',
        link: 'https://github.com/Agions/VideoForge',
      },
    ],

    sidebar: {
      '/': [
        { text: '首页', items: [{ text: '首页', link: '/' }] },
        { text: '功能', items: [{ text: '功能', link: '/features' }] },
        { text: 'AI 模型', items: [{ text: 'AI 模型', link: '/ai-models' }] },
        { text: '参考', items: [
          { text: '架构', link: '/architecture' },
          { text: '安全', link: '/security' },
          { text: 'FAQ', link: '/faq' },
          { text: '贡献', link: '/contributing' },
        ]},
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/VideoForge' },
    ],

    footer: {
      message: 'MIT License',
      copyright: 'Copyright © 2025-2026 Agions.',
    },
  },
})
