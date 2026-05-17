import { Link } from 'react-router-dom'
import { Target, BarChart3, Users, CheckSquare, ArrowRight, Check, ChevronDown, Zap } from 'lucide-react'
import { useState } from 'react'

import logoSvg        from '../static/logo.svg'
import joyfulEmployee from '../static/joyful_emloyee.jpg'
import officeChatting from '../static/office-chatting.jpg'

// ── Navbar ────────────────────────────────────────────────────────────────────
function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    setMenuOpen(false)
  }

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <img src={logoSvg} alt="AtomQuest" className="h-8 w-auto" />
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-slate-400">
          <button onClick={() => scrollTo('features')}    className="hover:text-slate-100 transition-colors">Features</button>
          <button onClick={() => scrollTo('how-it-works')} className="hover:text-slate-100 transition-colors">How it works</button>
          <button onClick={() => scrollTo('pricing')}     className="hover:text-slate-100 transition-colors">Pricing</button>
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-slate-100 hover:bg-slate-800/60 transition-all"
          >
            Log in
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-primary-500 hover:bg-primary-600 text-white transition-all shadow-sm"
          >
            Get started
          </Link>
          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-all"
          >
            <ChevronDown size={18} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-slate-800/80 bg-slate-950/95 px-4 py-3 space-y-1">
          {['features', 'how-it-works', 'pricing'].map(id => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className="block w-full text-left px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 capitalize transition-all"
            >
              {id.replace('-', ' ')}
            </button>
          ))}
          <Link to="/login" className="block px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-all">
            Log in
          </Link>
        </div>
      )}
    </header>
  )
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function Hero() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-primary-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          {/* Left — text */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-medium mb-6">
              <Zap size={12} />
              Goal tracking, simplified
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-slate-50 leading-tight tracking-tight mb-6">
              Set goals.
              <br />Track progress.
              <br /><span className="text-primary-400">Ship results.</span>
            </h1>

            <p className="text-lg text-slate-400 mb-10 leading-relaxed">
              AtomQuest helps teams align on objectives, run structured check-ins, and see exactly where every goal stands — without the complexity of enterprise tools.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-semibold bg-primary-500 hover:bg-primary-600 text-white transition-all shadow-lg shadow-primary-500/20"
              >
                Start for free <ArrowRight size={16} />
              </Link>
              <button
                onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-medium text-slate-300 hover:text-slate-100 hover:bg-slate-800/60 transition-all"
              >
                See how it works
              </button>
            </div>
          </div>

          {/* Right — photo */}
          <div className="relative">
            {/* Decorative ring */}
            <div className="absolute -inset-4 rounded-3xl bg-primary-500/5 border border-primary-500/10" />
            <img
              src={joyfulEmployee}
              alt="Happy employee using AtomQuest"
              className="relative rounded-2xl w-full object-cover shadow-2xl"
              style={{ maxHeight: '480px', objectPosition: 'center top' }}
            />
            {/* Floating stat card */}
            <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-sm border border-slate-700/60 rounded-xl px-4 py-3 shadow-xl">
              <p className="text-xs text-slate-400 mb-0.5">Goals on track</p>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-slate-50">92%</span>
                <span className="text-xs text-emerald-400 mb-0.5">↑ this cycle</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

// ── Features ──────────────────────────────────────────────────────────────────
const FEATURES = [
  {
    icon: Target,
    title: 'Goal management',
    desc: 'Create, assign, and track goals across individuals, teams, and departments. Set targets, weightages, and due dates in one place.',
  },
  {
    icon: CheckSquare,
    title: 'Structured check-ins',
    desc: 'Run quarterly check-ins with progress updates and manager approvals. Keep everyone accountable without endless meetings.',
  },
  {
    icon: Users,
    title: 'Role-based access',
    desc: 'Admins, managers, employees, and viewers each see exactly what they need. No configuration headaches.',
  },
  {
    icon: BarChart3,
    title: 'Progress reports',
    desc: 'Visual dashboards show goal completion rates, team performance, and cycle summaries at a glance.',
  },
  {
    icon: Zap,
    title: 'Approval workflows',
    desc: 'Goals and check-ins go through a lightweight approval flow so managers stay in the loop without micromanaging.',
  },
  {
    icon: Users,
    title: 'Team hierarchy',
    desc: 'Model your org structure with departments, reporting lines, and shared goals that cascade across teams.',
  },
]

function Features() {
  return (
    <section id="features" className="py-20 sm:py-24 border-t border-slate-800/60">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-50 mb-4">Everything your team needs</h2>
          <p className="text-slate-400 max-w-xl mx-auto">Built for the way modern teams actually work — not for enterprise procurement committees.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="glass-card p-6 hover:border-slate-600/50 transition-all duration-200">
              <div className="w-10 h-10 rounded-xl bg-primary-500/15 border border-primary-500/20 flex items-center justify-center mb-4">
                <Icon size={18} className="text-primary-400" />
              </div>
              <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── How it works ──────────────────────────────────────────────────────────────
const STEPS = [
  {
    step: '01',
    title: 'Admin sets up the org',
    desc: 'Create departments, add users, assign roles, and open a goal cycle — takes about 10 minutes.',
  },
  {
    step: '02',
    title: 'Teams set their goals',
    desc: 'Employees and managers create goals with targets and weightages. Managers review and approve.',
  },
  {
    step: '03',
    title: 'Check in every quarter',
    desc: 'Submit progress updates at each check-in milestone. Managers approve or request revisions.',
  },
  {
    step: '04',
    title: 'Review and improve',
    desc: "End-of-cycle reports show what worked, what didn't, and where to focus next.",
  },
]

function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-20 sm:py-28 border-t border-slate-800/60 overflow-hidden">
      {/* Background photo with dark overlay */}
      <div className="absolute inset-0">
        <img
          src={officeChatting}
          alt=""
          aria-hidden="true"
          className="w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-slate-950/85" />
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-50 mb-4">Up and running in minutes</h2>
          <p className="text-slate-300 max-w-xl mx-auto">No 6-week onboarding. No consultant required.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {STEPS.map(({ step, title, desc }, i) => (
            <div key={step} className="relative">
              {i < STEPS.length - 1 && (
                <div className="hidden lg:block absolute top-5 left-full w-full h-px bg-gradient-to-r from-slate-600 to-transparent z-0" />
              )}
              <div className="relative z-10 bg-slate-900/70 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-5">
                <div className="w-10 h-10 rounded-xl bg-primary-500/20 border border-primary-500/30 flex items-center justify-center mb-4">
                  <span className="text-xs font-bold text-primary-400">{step}</span>
                </div>
                <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── Pricing ───────────────────────────────────────────────────────────────────
const PLANS = [
  {
    name: 'Starter',
    price: 4,
    period: 'per user / month',
    desc: 'For small teams getting started with goal tracking.',
    features: [
      'Up to 25 users',
      'Unlimited goals & check-ins',
      'Role-based access',
      'Quarterly reports',
      'Email support',
    ],
    cta: 'Get started',
    highlight: false,
  },
  {
    name: 'Team',
    price: 8,
    period: 'per user / month',
    desc: 'For growing teams that need more control and visibility.',
    features: [
      'Unlimited users',
      'Everything in Starter',
      'Department hierarchies',
      'Shared goals',
      'Approval workflows',
      'Priority support',
    ],
    cta: 'Start free trial',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: null,
    period: 'custom pricing',
    desc: 'For large orgs with custom requirements.',
    features: [
      'Everything in Team',
      'SSO / SAML',
      'Custom integrations',
      'Dedicated onboarding',
      'SLA guarantee',
    ],
    cta: 'Contact us',
    highlight: false,
  },
]

function Pricing() {
  return (
    <section id="pricing" className="py-20 sm:py-24 border-t border-slate-800/60">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-50 mb-4">Simple, honest pricing</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Up to 50% less than Jira. No hidden fees, no per-feature paywalls.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map(({ name, price, period, desc, features, cta, highlight }) => (
            <div
              key={name}
              className={`rounded-2xl p-7 border transition-all duration-200 ${
                highlight
                  ? 'bg-primary-500/10 border-primary-500/40 shadow-xl shadow-primary-500/10 relative'
                  : 'bg-slate-800/40 border-slate-700/50'
              }`}
            >
              {highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary-500 text-white text-xs font-semibold">
                  Most popular
                </div>
              )}
              <div className="mb-5">
                <h3 className="font-semibold text-slate-100 text-lg mb-1">{name}</h3>
                <p className="text-sm text-slate-400">{desc}</p>
              </div>
              <div className="mb-6">
                {price !== null ? (
                  <>
                    <span className="text-4xl font-bold text-slate-50">${price}</span>
                    <span className="text-sm text-slate-400 ml-2">{period}</span>
                  </>
                ) : (
                  <span className="text-2xl font-bold text-slate-50">Custom</span>
                )}
              </div>
              <ul className="space-y-2.5 mb-7">
                {features.map(f => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <Check size={14} className="text-primary-400 mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                to="/login"
                className={`block text-center px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  highlight
                    ? 'bg-primary-500 hover:bg-primary-600 text-white shadow-sm'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                }`}
              >
                {cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── CTA Banner ────────────────────────────────────────────────────────────────
function CTABanner() {
  return (
    <section className="py-20 border-t border-slate-800/60">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold text-slate-50 mb-4">
          Ready to align your team?
        </h2>
        <p className="text-slate-400 mb-8">
          Get started in minutes. No credit card required.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl text-base font-semibold bg-primary-500 hover:bg-primary-600 text-white transition-all shadow-lg shadow-primary-500/20"
        >
          Get started for free <ArrowRight size={16} />
        </Link>
      </div>
    </section>
  )
}

// ── Footer ────────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-slate-800/60 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <img src={logoSvg} alt="AtomQuest" className="h-7 w-auto" />
        <p className="text-xs text-slate-600">© {new Date().getFullYear()} AtomQuest. All rights reserved.</p>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <a href="#" className="hover:text-slate-300 transition-colors">Privacy</a>
          <a href="#" className="hover:text-slate-300 transition-colors">Terms</a>
        </div>
      </div>
    </footer>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home() {
  return (
    <div className="gradient-bg min-h-screen">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Pricing />
      <CTABanner />
      <Footer />
    </div>
  )
}
