/**
 * Voxplore VitePress Theme
 */

import { h } from 'vue'
import { onMounted } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import './style.css'

// ─── Custom Components ────────────────────────────────────────
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
      h('div', { class: 'tip-card-body' }, this.$slots.default?.()),
    ])
  },
}

// ─── Browser-only helpers ─────────────────────────────────────
function setupScrollReveal() {
  if (typeof window === 'undefined') return

  const css = `
.vp-proof-bar{opacity:0;transform:translateY(10px);transition:opacity .5s ease,transform .5s ease}
.vp-proof-bar.revealed{opacity:1;transform:translateY(0)}
.nf-section-title{opacity:0;transform:translateX(-12px);transition:opacity .5s ease,transform .5s ease}
.nf-section-title.revealed{opacity:1;transform:translateX(0)}
.nf-workflow-step{opacity:0;transform:translateY(20px);transition:opacity .45s ease,transform .45s ease}
.nf-workflow-step.revealed{opacity:1;transform:translateY(0)}
.nf-workflow-arrow{opacity:0;transition:opacity .4s ease}
.nf-workflow-arrow.revealed{opacity:1}
.nf-why-card{opacity:0;transform:translateY(20px);transition:opacity .45s ease,transform .45s ease}
.nf-why-card.revealed{opacity:1;transform:translateY(0)}
.nf-why-card:hover{transform:translateY(-4px)!important;box-shadow:0 12px 40px rgba(10,132,255,.18)!important;border-color:rgba(10,132,255,.5)!important}
.nf-start-card{opacity:0;transform:translateY(20px);transition:opacity .45s ease,transform .45s ease}
.nf-start-card.revealed{opacity:1;transform:translateY(0)}
.nf-start-card:hover{transform:translateY(-3px)!important}
.vp-doc table tbody tr{opacity:0;transform:translateX(-8px);transition:opacity .4s ease,transform .4s ease}
.vp-doc table tbody tr.revealed{opacity:1;transform:translateX(0)}
`
  const s = document.createElement('style')
  s.textContent = css
  document.head.appendChild(s)

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -32px 0px' }
  )

  const groups = [
    '.vp-proof-bar',
    '.nf-why-grid .nf-why-card',
    '.nf-start-grid .nf-start-card',
    '.nf-workflow-step',
    '.nf-workflow-arrow',
    '.nf-section-title',
    '.vp-doc table tbody tr',
  ]

  groups.forEach(selector => {
    document.querySelectorAll(selector).forEach((el) => {
      const parent = el.closest('.VPFeatures, .nf-why-grid, .nf-start-grid')
      if (parent) {
        const siblings = Array.from(parent.querySelectorAll(el.className.split(' ')[0]))
        const idx = siblings.indexOf(el)
        ;(el as HTMLElement).style.transitionDelay = `${idx * 0.07}s`
      }
      observer.observe(el)
    })
  })
}

function setupNavScroll() {
  if (typeof window === 'undefined') return
  const nav = document.querySelector('.VPNav') as HTMLElement | null
  if (!nav) return
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60)
  }, { passive: true })
}

function setupTaglineCursor() {
  if (typeof window === 'undefined') return
  const tagline = document.querySelector('.vp-hero .tagline') as HTMLElement | null
  if (tagline) tagline.style.animation = 'vp-typing-cursor 1s step-end infinite'
}

// ─── Theme export ─────────────────────────────────────────────
export default {
  extends: DefaultTheme,

  enhanceApp({ app }) {
    app.component('TipCard', TipCard)

    onMounted(() => {
      setupScrollReveal()
      setupNavScroll()
      setupTaglineCursor()
    })
  },
} satisfies Theme