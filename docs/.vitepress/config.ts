import { defineConfig } from 'vitepress'

export default defineConfig({
  cleanUrls: false,
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
      { text: '首页', link: "/index.html" },
      { text: '功能', link: "/features.html" },
      { text: 'AI 模型', link: "/ai-models.html" },
      { text: 'FAQ', link: "/faq.html" },
      { text: '架构', link: "/architecture.html" },
      { text: '安全', link: "/security.html" },
      { text: '贡献', link: "/contributing.html" },
      {
        text: 'GitHub',
        link: 'https://github.com/Agions/Narrafiilm',
      },
    ],

    sidebar: {
      '/': [
        { text: '首页', items: [{ text: '首页', link: "/index.html" }] },
        { text: '功能', items: [{ text: '功能', link: "/features.html" }] },
        { text: 'AI 模型', items: [{ text: 'AI 模型', link: "/ai-models.html" }] },
        { text: '参考', items: [
          { text: '架构', link: "/architecture.html" },
          { text: '安全', link: "/security.html" },
          { text: 'FAQ & 疑难排查', link: "/faq.html" },
          { text: '贡献', link: "/contributing.html" },
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
