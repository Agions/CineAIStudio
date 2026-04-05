import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Narrafiilm',
  description: 'AI 驱动的专业视频创作桌面应用',
  base: '/Narrafiilm/',
  lang: 'en-US',
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/Narrafiilm/logo.png' }],
  ],

  themeConfig: {
    logo: '/Narrafiilm/logo.png',
    siteTitle: 'Narrafiilm',

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
        link: 'https://github.com/Agions/Narrafiilm',
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
          { text: 'FAQ & 疑难排查', link: '/faq' },
          { text: '贡献', link: '/contributing' },
        ]},
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
