import { useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, Check, ChevronRight, CircleDollarSign, FileCheck2, Gauge, LayoutDashboard, Menu, Play, Search, ShieldCheck, Sparkles, Target, WalletCards, Zap } from 'lucide-react'
import { getCases, getMetrics, runBatch, verifyCase, type BackendCase, type Metrics } from './api'

type Page = 'Command center' | 'Cases' | 'Exceptions' | 'Experiments' | 'Policy center'
type Status = 'Recovered' | 'In review' | 'Retrying' | 'Stopped'
type Case = { id: string; customer: string; merchant: string; amount: number; reason: string; probability: number; attempts: number; status: Status; date: string }
const fallback: Case[] = [
  { id: 'EVT_0001', customer: 'Customer 1', merchant: 'Spotify', amount: 199, reason: 'Insufficient funds', probability: .61, attempts: 1, status: 'Recovered', date: 'Today' },
  { id: 'EVT_0002', customer: 'Customer 2', merchant: 'Netflix India', amount: 4999, reason: 'Insufficient funds', probability: .58, attempts: 1, status: 'Recovered', date: 'Today' },
  { id: 'EVT_0003', customer: 'Customer 3', merchant: 'GymFlex', amount: 4999, reason: 'Insufficient funds', probability: .62, attempts: 4, status: 'In review', date: 'Today' },
]
const money = (value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
const mapCase = (item: BackendCase): Case => ({
  id: item.event_id, customer: item.customer_name || 'Unknown customer', merchant: item.merchant_name,
  amount: item.amount_inr, reason: item.diagnosed_class || 'Payment failure', probability: item.recovery_probability || 0,
  attempts: item.attempts, status: item.status === 'recovered' ? 'Recovered' : item.status === 'needs_human' ? 'In review' : item.status === 'stopped' ? 'Stopped' : 'Retrying',
  date: item.created_at ? new Date(item.created_at).toLocaleString() : 'Recent',
})

export default function App() {
  const [page, setPage] = useState<Page>('Command center')
  const [open, setOpen] = useState(false)
  const [cases, setCases] = useState<Case[]>(fallback)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [toast, setToast] = useState('')
  const [query, setQuery] = useState('')
  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(''), 2800) }
  const refresh = async () => {
    const [backendCases, backendMetrics] = await Promise.all([getCases(), getMetrics()])
    setCases(backendCases.map(mapCase)); setMetrics(backendMetrics)
  }
  useEffect(() => { refresh().catch(() => notify('Backend unavailable. Showing sample data.')) }, [])
  const verify = async (id: string) => {
    try {
      const updated = await verifyCase(id)
      setCases(current => current.map(item => item.id === id ? mapCase(updated) : item))
      setMetrics(await getMetrics())
      notify(`${id} verified. Dashboard updated.`)
    } catch { notify('Verification failed. Check that the backend API is running.') }
  }
  const batch = async () => {
    try { await runBatch(); await refresh(); notify('Recovery batch completed. Dashboard refreshed.') }
    catch { notify('Batch failed. Check that the backend API is running.') }
  }
  const pending = cases.filter(item => item.status === 'In review').length
  const nav: [Page, typeof LayoutDashboard][] = [['Command center', LayoutDashboard], ['Cases', FileCheck2], ['Exceptions', AlertTriangle], ['Experiments', Target], ['Policy center', ShieldCheck]]
  return <div className="app">
    <aside className={`sidebar ${open ? 'open' : ''}`}><div className="brand"><div className="mark"><Sparkles size={18}/></div><div><b>AAROHAN<span>-X</span></b><small>REVENUE RECOVERY OS</small></div></div>
      <div className="workspace"><i/> Acme subscriptions <ChevronRight size={14}/></div><nav>{nav.map(([label, Icon]) => <button key={label} className={page === label ? 'active' : ''} onClick={() => { setPage(label); setOpen(false) }}><Icon size={18}/>{label}{label === 'Exceptions' && pending > 0 && <em>{pending}</em>}</button>)}</nav>
      <div className="side-bottom"><div className="system"><b><i/> AI systems operational</b><small>Live backend connection</small></div><div className="user"><strong>KS</strong><span>Kripalu Sonar<small>Admin</small></span></div></div>
    </aside>
    <main><header><button className="mobile" onClick={() => setOpen(!open)}><Menu/></button><div className="crumb">⌘ Aarohan-X <ChevronRight size={14}/><b>{page}</b></div><div className="top-right"><span className="live"><i/> Live mode</span><strong>KS</strong></div></header>
      <section className="content">{page === 'Command center' && <Command metrics={metrics} onBatch={batch}/>} {page === 'Cases' && <CasesPage cases={cases} query={query} setQuery={setQuery} onVerify={verify}/>} {page === 'Exceptions' && <Exceptions cases={cases} onVerify={verify}/>} {page === 'Experiments' && <Experiments onRun={batch}/>} {page === 'Policy center' && <Policy/>}</section>
    </main>{toast && <div className="toast"><Check size={17}/>{toast}</div>}
  </div>
}

function Title({ eyebrow, title, desc, action }: { eyebrow: string; title: string; desc: string; action?: React.ReactNode }) { return <div className="title"><div><small>{eyebrow}</small><h1>{title}</h1><p>{desc}</p></div><div className="title-actions">{action}</div></div> }
function Stat({ label, value, icon: Icon, tone = '' }: { label: string; value: string; icon: typeof WalletCards; tone?: string }) { return <div className={`stat ${tone}`}><div><span>{label}</span><Icon size={17}/></div><b>{value}</b></div> }
function Command({ metrics, onBatch }: { metrics: Metrics | null; onBatch: () => void }) {
  const risk = (metrics?.total_at_risk_paise || 1059500) / 100, recovered = (metrics?.gross_recovered_paise || 0) / 100, net = (metrics?.net_recovered_paise || 0) / 100
  const rate = risk ? `${((recovered / risk) * 100).toFixed(1)}%` : '0.0%'
  return <><Title eyebrow="RECOVERY OPERATIONS" title="Revenue command center" desc="Live recovery performance from the backend database." action={<button className="primary" onClick={onBatch}><Play size={15} fill="currentColor"/> Run recovery batch</button>}/><div className="stats"><Stat label="Total at risk" value={money(risk)} icon={CircleDollarSign}/><Stat label="Gross recovered" value={money(recovered)} icon={WalletCards} tone="green"/><Stat label="Recovery rate" value={rate} icon={Gauge} tone="cyan"/><Stat label="Net recovered" value={money(net)} icon={Zap} tone="amber"/></div><section className="card"><div className="head"><div><small>LIVE STATUS</small><h2>Backend results</h2></div></div><p>{metrics?.events_recovered || 0} recovered · {metrics?.events_needs_human || 0} awaiting human verification</p></section></>
}
function CasesPage({ cases, query, setQuery, onVerify }: { cases: Case[]; query: string; setQuery: (value: string) => void; onVerify: (id: string) => void }) {
  const filtered = useMemo(() => cases.filter(item => `${item.id} ${item.customer} ${item.merchant}`.toLowerCase().includes(query.toLowerCase())), [cases, query])
  return <><Title eyebrow="CASE MANAGEMENT" title="Recovery cases" desc="Backend-backed payment events and outcomes."/><section className="card table-card"><div className="table-tools"><div className="search"><Search size={16}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search cases..."/></div></div><div className="table-wrap"><table><thead><tr><th>Case</th><th>Customer / merchant</th><th>Amount</th><th>Diagnosis</th><th>Status</th><th/></tr></thead><tbody>{filtered.map(item => <tr key={item.id}><td><code>{item.id}</code><small>{item.date}</small></td><td><b>{item.customer}</b><small>{item.merchant}</small></td><td><b>{money(item.amount)}</b></td><td>{item.reason}</td><td><span className={`status ${item.status.toLowerCase().replace(' ', '-')}`}><i/>{item.status}</span></td><td>{item.status === 'In review' && <button className="table-verify" onClick={() => onVerify(item.id)}>Verify</button>}</td></tr>)}</tbody></table></div></section></>
}
function Exceptions({ cases, onVerify }: { cases: Case[]; onVerify: (id: string) => void }) { const pending = cases.filter(item => item.status === 'In review'); return <><Title eyebrow="HUMAN-IN-THE-LOOP" title="Exceptions & verification" desc="Verify outcomes and update recovery analytics."/><div className="exception-banner"><AlertTriangle size={22}/><div><b>{pending.length} case{pending.length === 1 ? '' : 's'} requires attention</b><small>Verified outcomes are saved to the backend.</small></div></div><section className="card"><div className="head"><div><small>OPEN REVIEWS</small><h2>Verification queue</h2></div></div>{pending.length ? pending.map(item => <div className="exception" key={item.id}><span><b>{item.customer} · {item.merchant}</b><small>{item.id} · {money(item.amount)} at risk</small></span><button className="verify" onClick={() => onVerify(item.id)}><Check size={13}/> Verify outcome</button></div>) : <p>No cases require verification.</p>}</section></> }
function Experiments({ onRun }: { onRun: () => void }) { return <><Title eyebrow="STRATEGY LAB" title="Recovery experiments" desc="Run the deterministic five-event comparison." action={<button className="primary" onClick={onRun}><Play size={15} fill="currentColor"/> Run experiment</button>}/><section className="card"><h2>Full recovery ladder</h2><p>Silent retry first, then customer contact only when it creates positive expected value.</p></section></> }
function Policy() { return <><Title eyebrow="GUARDRAILS" title="Policy center" desc="Merchant-approved automation boundaries."/><section className="card policy-note"><ShieldCheck size={18}/><span><b>Safe by default</b><small>High-value cases enter human verification before money-touching actions.</small></span></section></> }
