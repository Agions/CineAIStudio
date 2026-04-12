import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Narrafiilm',
  description: 'AI 驱动的第一人称视频解说工具 — 上传视频，AI 代入主角视角，一键生成电影感配音解说。Qwen2.5-VL + DeepSeek-V3 + Edge-TTS。',
  base: '/Narrafiilm/',
  lang: 'zh-CN',
  cleanUrls: false,
  ignoreDeadLinks: true,

  head: [
    // Favicon
    ['link', { rel: 'icon', type: 'image/png', href: '/logo.png' }],
    // SEO
    ['meta', { name: 'keywords', content: 'AI视频解说,第一人称视频,自动配音,AI字幕,视频剪辑,NARRAFILM,DeepSeek,Qwen,Edge-TTS' }],
    ['meta', { name: 'author', content: 'Agions' }],
    // Open Graph
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Narrafiilm — AI First-Person Video Narrator' }],
    ['meta', { property: 'og:description', content: '上传视频，AI 代入主角视角，一键生成电影感配音解说' }],
    ['meta', { property: 'og:image', content: 'https://agions.github.io/Narrafiilm/logo.png' }],
    ['meta', { property: 'og:url', content: 'https://agions.github.io/Narrafiilm/' }],
    // Twitter Card
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:title', content: 'Narrafiilm — AI First-Person Video Narrator' }],
    ['meta', { name: 'twitter:description', content: '上传视频，AI 代入主角视角，一键生成电影感配音解说' }],
    // Theme
    ['meta', { name: 'theme-color', content: '#070B12' }],
  ],

  markdown: {
    lineNumbers: false,
  },

  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'Narrafiilm',

    // 深色/浅色模式切换（默认深色）
    appearance: 'dark',

    // 导航栏
    nav: [
      { text: '首页', link: '/' },
      { text: '功能介绍', link: '/features' },
      {
        text: '快速开始',
        items: [
          { text: '5 分钟上手', link: '/guide/quick-start' },
          { text: '完整安装指南', link: '/guide/installation' },
          { text: 'AI 配置', link: '/guide/ai-configuration' },
        ],
      },
      {
        text: '教程',
        items: [
          { text: 'AI 工作流详解', link: '/guide/ai-video-guide' },
          { text: '导出格式', link: '/guide/exporting' },
          { text: '界面介绍', link: '/guide/interface' },
        ],
      },
      {
        text: '参考',
        items: [
          { text: 'AI 模型', link: '/ai-models' },
          { text: '模型更新', link: '/model-updates' },
          { text: '疑难排查', link: '/guide/troubleshooting' },
          { text: '架构概览', link: '/architecture' },
        ],
      },
      {
        text: '更多',
        items: [
          { text: '安全设计', link: '/security' },
          { text: '贡献指南', link: '/contributing' },
          { text: 'FAQ', link: '/faq' },
        ],
      },
      {
        text: 'GitHub',
        link: 'https://github.com/Agions/Narrafiilm',
      },
    ],

    // 侧边栏
    sidebar: {
      '/guide/': [
        {
          text: '快速入门',
          items: [
            { text: '5 分钟快速开始', link: '/guide/quick-start' },
            { text: '完整安装指南', link: '/guide/installation' },
            { text: '界面介绍', link: '/guide/interface' },
          ],
        },
        {
          text: '核心教程',
          items: [
            { text: 'AI 工作流详解', link: '/guide/ai-video-guide' },
            { text: 'AI 配置指南', link: '/guide/ai-configuration' },
            { text: '导出格式', link: '/guide/exporting' },
          ],
        },
        {
          text: '疑难解答',
          items: [
            { text: '常见问题 FAQ', link: '/faq' },
            { text: '疑难排查', link: '/guide/troubleshooting' },
          ],
        },
      ],
      '/': [
        {
          text: '入门',
          items: [
            { text: '首页', link: '/' },
            { text: '快速开始', link: '/guide/quick-start' },
            { text: '功能介绍', link: '/features' },
          ],
        },
        {
          text: '快速开始',
          items: [
            { text: '5 分钟上手', link: '/guide/quick-start' },
            { text: '完整安装', link: '/guide/installation' },
            { text: '界面介绍', link: '/guide/interface' },
          ],
        },
        {
          text: 'AI 工作流',
          items: [
            { text: '工作流详解', link: '/guide/ai-video-guide' },
            { text: 'AI 模型配置', link: '/guide/ai-configuration' },
            { text: '导出格式', link: '/guide/exporting' },
          ],
        },
        {
          text: '参考',
          items: [
            { text: 'AI 模型', link: '/ai-models' },
            { text: '模型更新', link: '/model-updates' },
            { text: '架构概览', link: '/architecture' },
            { text: '安全设计', link: '/security' },
          ],
        },
        {
          text: '社区',
          items: [
            { text: '常见问题', link: '/faq' },
            { text: '贡献指南', link: '/contributing' },
            { text: '疑难排查', link: '/guide/troubleshooting' },
          ],
        },
      ],
    },

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/Agions/Narrafiilm/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面',
    },

    // 最后更新时间
    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'short',
      },
    },

    // 本地搜索
    search: {
      provider: 'local',
      options: {
        placeholder: '搜索文档...',
        translations: {
          button: {
            buttonText: '搜索',
            buttonAriaLabel: '搜索文档',
          },
        },
      },
    },

    // 返回顶部
    returnToTopLabel: '返回顶部',
    sidebarMenuLabel: '菜单',
    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },

    // 大纲
    outline: {
      level: [2, 3],
      label: '目录',
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/Narrafiilm' },
    ],

    // 页脚
    footer: {
      message: 'MIT License · Copyright © 2025-2026 Agions',
      copyright: 'Narrafiilm — AI First-Person Video Narrator · 开源免费 · 隐私优先',
    },
  },
})
