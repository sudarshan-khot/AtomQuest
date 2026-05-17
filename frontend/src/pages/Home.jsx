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
    <header className="sticky top-0 z-50 border-b border-cream-300 bg-white/95 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <img src={logoSvg} alt="" aria-hidden="true" className="h-8 w-auto" />
          <span className="font-bold text-graphite-900 text-lg tracking-tight">AtomQuest</span>
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-graphite-500">
          <button onClick={() => scrollTo('features')}     className="hover:text-graphite-900 transition-colors font-medium">Features</button>
          <button onClick={() => scrollTo('how-it-works')} className="hover:text-graphite-900 transition-colors font-medium">How it works</button>
          <button onClick={() => scrollTo('pricing')}      className="hover:text-graphite-900 transition-colors font-medium">Pricing</button>
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-graphite-600 hover:text-graphite-900 hover:bg-cream-200 transition-all"
          >
            Log in
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold bg-primary-500 hover:bg-primary-600 text-graphite-900 transition-all shadow-sm"
          >
            Get started
          </Link>
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="md:hidden p-2 rounded-lg text-graphite-500 hover:text-graphite-900 hover:bg-cream-200 transition-all"
          >
            <ChevronDown size={18} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-cream-200 bg-white px-4 py-3 space-y-1">
          {['features', 'how-it-works', 'pricing'].map(id => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className="block w-full text-left px-3 py-2 rounded-lg text-sm text-graphite-600 hover:text-graphite-900 hover:bg-cream-200 capitalize transition-all"
            >
              {id.replace('-', ' ')}
            </button>
          ))}
          <Link to="/login" className="block px-3 py-2 rounded-lg text-sm text-graphite-600 hover:text-graphite-900 hover:bg-cream-200 transition-all">
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
    <section className="relative overflow-hidden py-16 sm:py-24 bg-cream-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          {/* Left — text */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-100 border border-primary-200 text-primary-700 text-xs font-semibold mb-6">
              <Zap size={12} />
              Goal tracking, simplified
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-graphite-900 leading-tight tracking-tight mb-6">
              Set goals.
              <br />Track progress.
              <br /><span className="text-primary-600">Ship results.</span>
            </h1>

            <p className="text-lg text-graphite-500 mb-10 leading-relaxed">
              AtomQuest helps teams align on objectives, run structured check-ins, and see exactly where every goal stands — without the complexity of enterprise tools.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-semibold bg-primary-500 hover:bg-primary-600 text-graphite-900 transition-all shadow-md"
              >
                Start for free <ArrowRight size={16} />
              </Link>
              <button
                onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-medium text-graphite-600 hover:text-graphite-900 hover:bg-cream-200 border border-cream-300 transition-all"
              >
                See how it works
              </button>
            </div>
          </div>

          {/* Right — photo */}
          <div className="relative">
            <div className="absolute -inset-3 rounded-3xl bg-primary-100 border border-primary-200" />
            <img
              src={joyfulEmployee}
              alt="Happy employee using AtomQuest"
              className="relative rounded-2xl w-full object-cover shadow-xl"
              style={{ maxHeight: '480px', objectPosition: 'center top' }}
            />
            {/* Floating stat card */}
            <div className="absolute bottom-4 left-4 bg-white border border-cream-300 rounded-xl px-4 py-3 shadow-lg">
              <p className="text-xs text-graphite-400 mb-0.5">Goals on track</p>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-graphite-900">92%</span>
                <span className="text-xs text-green-600 font-medium mb-0.5">↑ this cycle</span>
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
    <section id="features" className="py-20 sm:py-24 bg-white border-t border-cream-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-graphite-900 mb-4">Everything your team needs</h2>
          <p className="text-graphite-500 max-w-xl mx-auto">Built for the way modern teams actually work — not for enterprise procurement committees.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="bg-cream-100 border border-cream-200 rounded-xl p-6 hover:border-graphite-300 hover:shadow-sm transition-all duration-200"
            >
              <div className="w-10 h-10 rounded-xl bg-graphite-900 flex items-center justify-center mb-4">
                <Icon size={18} className="text-primary-400" />
              </div>
              <h3 className="font-semibold text-graphite-900 mb-2">{title}</h3>
              <p className="text-sm text-graphite-500 leading-relaxed">{desc}</p>
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
    <section id="how-it-works" className="relative py-20 sm:py-28 overflow-hidden border-t border-cream-200">
      {/* Background photo with light overlay */}
      <div className="absolute inset-0">
        <img
          src={officeChatting}
          alt=""
          aria-hidden="true"
          className="w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-graphite-900/80" />
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Up and running in minutes</h2>
          <p className="text-graphite-300 max-w-xl mx-auto">No 6-week onboarding. No consultant required.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {STEPS.map(({ step, title, desc }, i) => (
            <div key={step} className="relative">
              {i < STEPS.length - 1 && (
                <div className="hidden lg:block absolute top-5 left-full w-full h-px bg-gradient-to-r from-primary-500/40 to-transparent z-0" />
              )}
              <div className="relative z-10 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-5">
                <div className="w-10 h-10 rounded-xl bg-primary-500 flex items-center justify-center mb-4">
                  <span className="text-xs font-bold text-graphite-900">{step}</span>
                </div>
                <h3 className="font-semibold text-white mb-2">{title}</h3>
                <p className="text-sm text-graphite-300 leading-relaxed">{desc}</p>
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
    <section id="pricing" className="py-20 sm:py-24 bg-cream-100 border-t border-cream-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-graphite-900 mb-4">Simple, honest pricing</h2>
          <p className="text-graphite-500 max-w-xl mx-auto">
            Up to 50% less than Jira. No hidden fees, no per-feature paywalls.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map(({ name, price, period, desc, features, cta, highlight }) => (
            <div
              key={name}
              className={`rounded-2xl p-7 border transition-all duration-200 ${
                highlight
                  ? 'bg-graphite-900 border-graphite-700 shadow-xl relative'
                  : 'bg-white border-cream-300'
              }`}
            >
              {highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary-500 text-graphite-900 text-xs font-bold">
                  Most popular
                </div>
              )}
              <div className="mb-5">
                <h3 className={`font-semibold text-lg mb-1 ${highlight ? 'text-white' : 'text-graphite-900'}`}>{name}</h3>
                <p className={`text-sm ${highlight ? 'text-graphite-400' : 'text-graphite-500'}`}>{desc}</p>
              </div>
              <div className="mb-6">
                {price !== null ? (
                  <>
                    <span className={`text-4xl font-bold ${highlight ? 'text-white' : 'text-graphite-900'}`}>${price}</span>
                    <span className={`text-sm ml-2 ${highlight ? 'text-graphite-400' : 'text-graphite-500'}`}>{period}</span>
                  </>
                ) : (
                  <span className={`text-2xl font-bold ${highlight ? 'text-white' : 'text-graphite-900'}`}>Custom</span>
                )}
              </div>
              <ul className="space-y-2.5 mb-7">
                {features.map(f => (
                  <li key={f} className={`flex items-start gap-2.5 text-sm ${highlight ? 'text-graphite-300' : 'text-graphite-600'}`}>
                    <Check size={14} className="text-primary-500 mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                to="/login"
                className={`block text-center px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  highlight
                    ? 'bg-primary-500 hover:bg-primary-600 text-graphite-900'
                    : 'bg-graphite-900 hover:bg-graphite-800 text-white'
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
    <section className="py-20 bg-graphite-900 border-t border-graphite-800">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
          Ready to align your team?
        </h2>
        <p className="text-graphite-400 mb-8">
          Get started in minutes. No credit card required.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl text-base font-semibold bg-primary-500 hover:bg-primary-600 text-graphite-900 transition-all shadow-lg"
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
    <footer className="border-t border-cream-200 bg-white py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <img src={logoSvg} alt="" aria-hidden="true" className="h-7 w-auto" />
          <span className="text-sm font-bold text-graphite-700">AtomQuest</span>
        </div>
        <p className="text-xs text-graphite-400">© {new Date().getFullYear()} AtomQuest. All rights reserved.</p>
        <div className="flex items-center gap-4 text-xs text-graphite-400">
          <a href="#" className="hover:text-graphite-700 transition-colors">Privacy</a>
          <a href="#" className="hover:text-graphite-700 transition-colors">Terms</a>
        </div>
      </div>
    </footer>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home() {
  return (
    <div className="min-h-screen bg-cream-100">
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
