import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'VideoForge',
  description: 'AI 驱动的专业视频创作桌面应用 — 全流程自动化剪辑',
  base: '/VideoForge/',
  lang: 'en-US',
  cleanUrls: false,
  lastUpdated: true,

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/VideoForge/logo.png' }],
    ['meta', { name: 'theme-color', content: '#10B981' }],
  ],

  themeConfig: {
    logo: '/VideoForge/logo.png',
    siteTitle: 'VideoForge',

    nav: [
      { text: '首页', link: '/' },
      {
        text: '指南',
        items: [
          { text: '快速开始', link: '/guide/quick-start' },
          { text: '安装配置', link: '/guide/installation' },
          { text: '界面介绍', link: '/guide/interface' },
          { text: '故障排除', link: '/guide/troubleshooting' },
        ],
      },
      { text: '功能', link: '/features' },
      { text: 'AI 模型', link: '/ai-models' },
      { text: 'FAQ', link: '/faq' },
      {
        text: '更多',
        items: [
          { text: '架构概览', link: '/architecture' },
          { text: '安全设计', link: '/security' },
          { text: '贡献指南', link: '/contributing' },
        ],
      },
      { text: 'GitHub', link: 'https://github.com/Agions/VideoForge' },
    ],

    sidebar: {
      '/': [
        {
          text: '快速导航',
          items: [
            { text: '首页', link: '/' },
            { text: '快速开始', link: '/guide/quick-start' },
            { text: '功能介绍', link: '/features' },
          ],
        },
        {
          text: 'AI 视频创作',
          items: [
            { text: 'AI 配置指南', link: '/guide/ai-configuration' },
            { text: 'AI 视频创作指南', link: '/guide/ai-video-guide' },
            { text: '导出格式详解', link: '/guide/exporting' },
          ],
        },
        {
          text: '使用指南',
          items: [
            { text: '安装配置', link: '/guide/installation' },
            { text: '界面介绍', link: '/guide/interface' },
            { text: '故障排除', link: '/guide/troubleshooting' },
            { text: '批量处理', link: '/guide/batch-processing' },
          ],
        },
        {
          text: '进阶主题',
          items: [
            { text: '插件开发', link: '/guide/plugin-development' },
            { text: '配置参考', link: '/config' },
          ],
        },
        {
          text: '参考',
          items: [
            { text: 'AI 模型', link: '/ai-models' },
            { text: '架构概览', link: '/architecture' },
            { text: '安全设计', link: '/security' },
            { text: '常见问题', link: '/faq' },
            { text: '贡献指南', link: '/contributing' },
          ],
        },
      ],
      '/guide/': [
        {
          text: '入门指南',
          items: [
            { text: '5 分钟快速开始', link: '/guide/quick-start' },
            { text: '安装配置', link: '/guide/installation' },
            { text: '界面介绍', link: '/guide/interface' },
          ],
        },
        {
          text: 'AI 创作',
          items: [
            { text: 'AI 配置指南', link: '/guide/ai-configuration' },
            { text: 'AI 视频创作指南', link: '/guide/ai-video-guide' },
            { text: '导出格式详解', link: '/guide/exporting' },
          ],
        },
        {
          text: '进阶功能',
          items: [
            { text: '批量处理', link: '/guide/batch-processing' },
            { text: '插件开发', link: '/guide/plugin-development' },
          ],
        },
        {
          text: '问题解决',
          items: [
            { text: '故障排除', link: '/guide/troubleshooting' },
          ],
        },
      ],
    },

    search: {
      provider: 'local',
      options: {
        placeholder: '搜索文档...',
        translations: {
          button: {
            buttonText: '搜索',
            buttonAriaLabel: '搜索',
          },
        },
      },
    },

    editLink: {
      pattern: 'https://github.com/Agions/VideoForge/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面',
    },

    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'short',
      },
    },

    returnToTopLabel: '返回顶部',
    sidebarMenuLabel: '菜单',

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Agions/VideoForge' },
      { icon: 'twitter', link: 'https://twitter.com/videoforge' },
    ],

    footer: {
      message: 'MIT License',
      copyright: 'Copyright © 2025-2026 Agions. 基于开源精神构建。',
    },
  },

  vite: {
    build: {
      rollupOptions: {
        output: {
          // 确保资源路径正确
        },
      },
    },
  },
})
