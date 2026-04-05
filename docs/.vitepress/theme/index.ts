/**
 * Narrafiilm VitePress Theme
 */

import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import './style.css'

// TipCard — 自定义提示卡片组件
const TipCard = {
  name: 'TipCard',
  props: {
    title: { type: String, required: true },
    icon: { type: String, default: '💡' },
  },
  render() {
    return h('div', { class: 'tip-card' }, [
      h('div', { class: 'tip-card-header' }, [
        h('span', { class: 'tip-card-icon' }, this.icon),
        h('span', { class: 'tip-card-title' }, this.title),
      ]),
      h('div', { class: 'tip-card-body' },
        this.$slots.default?.()
      ),
    ])
  },
}

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('TipCard', TipCard)
  },
} satisfies Theme
