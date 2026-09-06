import { Fragment, useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, Check, ChevronRight, CircleDollarSign, FileCheck2, Gauge, LayoutDashboard, ListChecks, Menu, Play, Search, ShieldCheck, Target, WalletCards, Zap } from 'lucide-react'
import { getAnalytics, getCases, getMetrics, getPolicy, runBatch, runExperiments, updatePolicy, verifyCase, type Analytics, type BackendCase, type ExperimentMetrics, type Metrics, type Policy as PolicyData } from './api'

type Page = 'Command center' | 'Cases' | 'PTP tracker' | 'Exceptions' | 'Experiments' | 'Policy center'
type Status = 'Recovered' | 'In review' | 'Retrying' | 'Stopped'
type Communication = { channel: 'text' | 'voice'; action: string; status: string; message?: string; transcript?: string; timestamp: string }
type Case = { id: string; customer: string; merchant: string; amount: number; reason: string; probability: number; attempts: number; status: Status; date: string; communications: Communication[]; phone?: string; failureCode?: string; failureDescription?: string; expectedGross: number; channelCost: number; netExpected: number; explanation?: string; ledger: { action: string; detail: Record<string, unknown>; timestamp: string; cost?: number; idempotency_key?: string | null }[]; ptp?: { promised_date: string | null; count: number; broken: boolean } }
const money = (value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
const mapCase = (item: BackendCase): Case => ({
  id: item.event_id, customer: item.customer_name || 'Unknown customer', merchant: item.merchant_name,
  amount: Number(item.amount_inr || 0), reason: item.diagnosed_class || 'Payment failure', probability: item.recovery_probability || 0,
  attempts: item.attempts || 0, status: item.status === 'recovered' ? 'Recovered' : item.status === 'needs_human' ? 'In review' : item.status === 'stopped' ? 'Stopped' : 'Retrying',
  date: item.created_at ? new Date(item.created_at).toLocaleString() : 'Recent',
  communications: item.communications || [],
  phone: item.customer_phone, failureCode: item.failure_code, failureDescription: item.failure_description,
  expectedGross: Number(item.expected_gross_value_inr || 0), channelCost: Number(item.channel_cost_inr || 0), netExpected: Number(item.net_expected_value_inr || 0),
  explanation: item.decision_explanation, ledger: item.ledger || [], ptp: item.ptp,
})

export default function App() {
  const [page, setPage] = useState<Page>('Command center')
  const [open, setOpen] = useState(false)
  const [cases, setCases] = useState<Case[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [toast, setToast] = useState('')
  const [query, setQuery] = useState('')
  const [experimentResults, setExperimentResults] = useState<Record<string, ExperimentMetrics> | null>(null)
  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(''), 2800) }
  const refresh = async () => {
    const [backendCases, backendMetrics, backendAnalytics] = await Promise.all([getCases(), getMetrics(), getAnalytics()])
    setCases(backendCases.map(mapCase)); setMetrics(backendMetrics); setAnalytics(backendAnalytics)
  }
  useEffect(() => {
    let mounted = true
    const sync = () => refresh().catch(() => { if (mounted) notify('Live data is temporarily unavailable. Retrying shortly.') })
    sync()
    const timer = window.setInterval(sync, 10000)
    return () => { mounted = false; window.clearInterval(timer) }
  }, [])
  const verify = async (id: string) => {
    try {
      const updated = await verifyCase(id)
      setCases(current => current.map(item => item.id === id ? mapCase(updated) : item))
      setMetrics(await getMetrics())
      setAnalytics(await getAnalytics())
      notify(`${id} verified. Dashboard updated.`)
    } catch { notify('Verification failed. Please try again or check the workspace connection.') }
  }
  const batch = async () => {
    try { await runBatch(); await refresh(); notify('Recovery batch completed. Dashboard refreshed.') }
    catch { notify('Recovery queue could not be processed. Please try again.') }
  }
  const pending = cases.filter(item => item.status === 'In review').length
  const nav: [Page, typeof LayoutDashboard][] = [['Command center', LayoutDashboard], ['Cases', FileCheck2], ['PTP tracker', ListChecks], ['Exceptions', AlertTriangle], ['Experiments', Target], ['Policy center', ShieldCheck]]
  return <div className="app">
    <aside className={`sidebar ${open ? 'open' : ''}`}><div className="brand"><div className="mark" aria-label="Aarohan-X logo"><svg viewBox="0 0 36 36" role="img" aria-hidden="true"><path className="logo-orbit" d="M8 22.5C9.7 28.1 15 32 21.1 32 28.2 32 34 26.2 34 19.1c0-2.1-.5-4.1-1.4-5.9"/><path className="logo-rise" d="M8.5 25.5 15 19l4.2 4.2L29 13.4"/><path className="logo-arrow" d="M23.2 13.4H29v5.8"/></svg></div><div><b>AAROHAN<span>-X</span></b><small>REVENUE RECOVERY OS</small></div></div>
      <div className="workspace"><i/> Acme subscriptions <ChevronRight size={14}/></div><nav>{nav.map(([label, Icon]) => <button key={label} className={page === label ? 'active' : ''} onClick={() => { setPage(label); setOpen(false) }}><Icon size={18}/>{label}{label === 'Exceptions' && pending > 0 && <em>{pending}</em>}</button>)}</nav>
      <div className="side-bottom"><div className="system"><b><i/> All systems operational</b><small>Recovery services connected</small></div><div className="user"><strong>KS</strong><span>Kripalu Sonar<small>Administrator</small></span></div></div>
    </aside>
    <main><header><button className="mobile" onClick={() => setOpen(!open)}><Menu/></button><div className="crumb">⌘ Aarohan-X <ChevronRight size={14}/><b>{page}</b></div><div className="top-right"><span className="live"><i/> Workspace live</span><strong>KS</strong></div></header>
      <section className="content">{page === 'Command center' && <Command cases={cases} metrics={metrics} analytics={analytics} onBatch={batch}/>} {page === 'Cases' && <CasesPage cases={cases} query={query} setQuery={setQuery} onVerify={verify}/>} {page === 'PTP tracker' && <PtpTracker cases={cases}/>} {page === 'Exceptions' && <Exceptions cases={cases} onVerify={verify}/>} {page === 'Experiments' && <Experiments results={experimentResults} onRun={async () => { try { setExperimentResults(await runExperiments()); notify('Strategy experiment completed.')} catch { notify('Experiment could not be completed. Please try again.') } }}/>} {page === 'Policy center' && <Policy notify={notify}/>}</section>
    </main><RecoveryCopilot cases={cases} metrics={metrics}/>{toast && <div className="toast"><Check size={17}/>{toast}</div>}
  </div>
}

function RecoveryCopilot({ cases, metrics }: { cases: Case[]; metrics: Metrics | null }) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([{ from: 'bot', text: 'Hi! I can explain recovery results, human reviews, messages, and calls.' }])
  const answer = (question: string) => {
    const text = question.toLowerCase()
    const contacts = cases.reduce((sum, item) => sum + item.communications.length, 0)
    if (text.includes('human') || text.includes('review')) return `${metrics?.events_needs_human || cases.filter(item => item.status === 'In review').length} case(s) need human verification. Open Exceptions to review them.`
    if (text.includes('recover') || text.includes('net')) return `The current batch recovered ${money((metrics?.gross_recovered_paise || 0) / 100)} gross and ${money((metrics?.net_recovered_paise || 0) / 100)} net.`
    if (text.includes('message') || text.includes('text') || text.includes('call')) return `The batch recorded ${contacts} customer contact(s). Open Cases to see each Hinglish message or call transcript.`
    if (text.includes('why')) return 'The policy engine combines diagnosis, recovery probability, channel cost, retry limits, and safety gates. AI language generation cannot override those rules.'
    return 'Try asking: “How much was recovered?”, “Which cases need human review?”, or “Show messages and calls”.'
  }
  const send = () => { const question = input.trim(); if (!question) return; setMessages(current => [...current, { from: 'user', text: question }, { from: 'bot', text: answer(question) }]); setInput('') }
  return <div className={`copilot ${open ? 'open' : ''}`}><button className="copilot-toggle" aria-label="Open Recovery Copilot" title="Recovery Copilot" onClick={() => setOpen(!open)}>✦</button>{open && <div className="copilot-panel"><b>Recovery Copilot</b><div className="copilot-messages">{messages.map((message, index) => <div className={message.from} key={index}>{message.text}</div>)}</div><div className="copilot-input"><input value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && send()} placeholder="Ask about this batch..."/><button onClick={send}>Send</button></div></div>}</div>
}

function Title({ eyebrow, title, desc, action }: { eyebrow: string; title: string; desc: string; action?: React.ReactNode }) { return <div className="title"><div><small>{eyebrow}</small><h1>{title}</h1><p>{desc}</p></div><div className="title-actions">{action}</div></div> }
function Stat({ label, value, icon: Icon, tone = '' }: { label: string; value: string; icon: typeof WalletCards; tone?: string }) { return <div className={`stat ${tone}`}><div><span>{label}</span><Icon size={17}/></div><b>{value}</b></div> }
function Command({ cases, metrics, analytics, onBatch }: { cases: Case[]; metrics: Metrics | null; analytics: Analytics | null; onBatch: () => void }) {
  const risk = (metrics?.total_at_risk_paise || 0) / 100, recovered = (metrics?.gross_recovered_paise || 0) / 100, net = (metrics?.net_recovered_paise || 0) / 100
  const rate = risk ? `${((recovered / risk) * 100).toFixed(1)}%` : '0.0%'
  const communications = cases.flatMap(item => (item.communications || []).map(communication => ({ ...communication, id: item.id, customer: item.customer })))
  const callCount = communications.filter(communication => communication.channel === 'voice').length
  return <><Title eyebrow="RECOVERY OPERATIONS" title="Revenue command center" desc="Live performance across your payment recovery portfolio." action={<button className="primary" onClick={onBatch}><Play size={15} fill="currentColor"/> Process recovery queue</button>}/><div className="stats"><Stat label="Total at risk" value={money(risk)} icon={CircleDollarSign}/><Stat label="Gross recovered" value={money(recovered)} icon={WalletCards} tone="green"/><Stat label="Recovery rate" value={rate} icon={Gauge} tone="cyan"/><Stat label="Net recovered" value={money(net)} icon={Zap} tone="amber"/></div><section className="card insight-strip"><div><small>INCREMENTAL IMPACT</small><b>{money((metrics?.incremental_recovery_paise || 0) / 100)} above natural baseline</b><span>Baseline assumes 40% natural recovery · {metrics?.incremental_recovery_rate || 0}% incremental rate</span></div><div><small>PROMISE-TO-PAY</small><b>{metrics?.ptp_promises || 0} promises tracked</b><span>{metrics?.broken_ptps || 0} broken promises escalated</span></div><div><small>DECISION CONTROL</small><b>Cost-aware actions</b><span>Every action has EV, policy, and audit context</span></div></section><div className="dashboard-grid"><FunnelGraph funnel={analytics?.funnel || []}/><ActionGraph actions={analytics?.actions || []}/></div><section className="card"><div className="head"><div><small>CONTACT ACTIVITY</small><h2>Customer outreach</h2></div><small>{callCount} call{callCount === 1 ? '' : 's'} recorded</small></div>{communications.length ? <div className="contact-feed">{communications.map((communication, index) => <div key={`${communication.id}-${index}`}><b>{communication.channel === 'text' ? 'Text nudge' : communication.status === 'failed' ? 'Voice call attempted' : 'Voice call completed'} · {communication.id}</b><small>{communication.customer} · {communication.status}</small>{communication.message && <p>{communication.channel === 'voice' && communication.status === 'failed' ? `Call outcome: ${communication.message}` : communication.message}</p>}{communication.transcript && <p>{communication.channel === 'voice' ? 'Call transcript: ' : 'Message: '}{communication.transcript}</p>}</div>)}</div> : <p>No customer outreach recorded for this cycle.</p>}</section><section className="card"><div className="head"><div><small>DECISION EXPLAINABILITY</small><h2>How the recovery engine handled this cycle</h2></div></div><p>{metrics?.events_recovered || 0} recovered · {metrics?.events_needs_human || 0} awaiting human verification · {Object.values(analytics?.confidence || {}).reduce((sum, value) => sum + value, 0)} decisions scored</p></section></>
}
function FunnelGraph({ funnel }: { funnel: { label: string; value: number }[] }) {
  const max = Math.max(...funnel.map(item => item.value), 1)
  return <section className="card analytics-card"><div className="head"><div><small>RECOVERY FUNNEL</small><h2>Where value moves</h2></div></div><div className="bar-chart">{funnel.map(item => <div className="bar-row" key={item.label}><span>{item.label}</span><i><b style={{ width: `${(item.value / max) * 100}%` }}/></i><strong>{item.value}</strong></div>)}</div></section>
}
function ActionGraph({ actions }: { actions: { name: string; events: number; recovered_paise: number }[] }) {
  const max = Math.max(...actions.map(item => item.recovered_paise), 1)
  return <section className="card analytics-card"><div className="head"><div><small>POLICY PERFORMANCE</small><h2>Recovered value by action</h2></div></div><div className="bar-chart">{actions.length ? actions.map(item => <div className="bar-row" key={item.name}><span>{item.name.replace(/_/g, ' ')}</span><i><b className="bar-green" style={{ width: `${(item.recovered_paise / max) * 100}%` }}/></i><strong>{money(item.recovered_paise / 100)}</strong></div>) : <p>No actions recorded yet.</p>}</div></section>
}
function CasesPage({ cases, query, setQuery, onVerify }: { cases: Case[]; query: string; setQuery: (value: string) => void; onVerify: (id: string) => void }) {
  const filtered = useMemo(() => cases.filter(item => `${item.id} ${item.customer} ${item.merchant}`.toLowerCase().includes(query.toLowerCase())), [cases, query])
  return <><Title eyebrow="CASE MANAGEMENT" title="Recovery cases" desc="Monitor failed payments, customer outreach, and recovery outcomes."/><section className="card table-card"><div className="table-tools"><div className="search"><Search size={16}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search cases..."/></div></div><div className="table-wrap"><table><thead><tr><th>Case</th><th>Customer / merchant</th><th>Amount</th><th>Diagnosis</th><th>Contact activity</th><th>Status</th><th/></tr></thead><tbody>{filtered.map(item => <Fragment key={item.id}><tr><td><code>{item.id}</code><small>{item.date}</small></td><td><b>{item.customer}</b><small>{item.merchant}</small></td><td><b>{money(item.amount)}</b></td><td>{item.reason}</td><td>{item.communications.length ? `${item.communications.length} contact${item.communications.length === 1 ? '' : 's'}` : 'No contact'}</td><td><span className={`status ${item.status.toLowerCase().replace(' ', '-')}`}><i/>{item.status}</span></td><td>{item.status === 'In review' && <button className="table-verify" onClick={() => onVerify(item.id)}>Verify</button>}</td></tr>{(item.communications || []).map((communication, index) => <tr className="communication-row" key={`${item.id}-${communication.timestamp}-${index}`}><td/><td colSpan={6}><b>{communication.channel === 'text' ? 'Text nudge sent' : communication.status === 'failed' ? 'Voice call attempted' : 'Voice call completed'}</b><small>{communication.timestamp ? new Date(communication.timestamp).toLocaleString() : ''}</small>{communication.message && <p>{communication.channel === 'voice' && communication.status === 'failed' ? `Call outcome: ${communication.message}` : communication.message}</p>}{communication.transcript && <p>Call transcript: {communication.transcript}</p>}</td></tr>)}</Fragment>)}</tbody></table></div></section></>
}
function PtpTracker({ cases }: { cases: Case[] }) {
  const tracked = cases.filter(item => (item.ptp?.count || 0) > 0 || item.ledger.some(entry => entry.action === 'ptp_recorded' || entry.action === 'ptp_broken'))
  return <><Title eyebrow="PROMISE MANAGEMENT" title="Promise-to-pay tracker" desc="Track commitments, broken promises, and the next recovery decision."/><section className="card table-card"><div className="head"><div><small>COMMITMENT QUEUE</small><h2>{tracked.length} promises and follow-ups</h2></div></div>{tracked.length ? <div className="table-wrap"><table><thead><tr><th>Case</th><th>Customer</th><th>At risk</th><th>Promise date</th><th>Attempts</th><th>Status</th></tr></thead><tbody>{tracked.map(item => <tr key={item.id}><td><code>{item.id}</code><small>{item.merchant}</small></td><td>{item.customer}</td><td><b>{money(item.amount)}</b></td><td>{item.ptp?.promised_date ? new Date(item.ptp.promised_date).toLocaleDateString() : 'Recorded in timeline'}</td><td>{item.attempts}</td><td><span className={`status ${item.ptp?.broken ? 'stopped' : 'retrying'}`}><i/>{item.ptp?.broken ? 'Broken · escalated' : 'Active commitment'}</span></td></tr>)}</tbody></table></div> : <div className="review-empty"><ListChecks size={20}/><b>No promise-to-pay commitments recorded.</b><span>Voice and text outcomes will appear here when a customer commits to a payment date.</span></div>}</section><section className="card"><div className="head"><div><small>RECOVERY TIMELINE</small><h2>Auditable event history</h2></div></div><div className="audit-timeline">{cases.slice(0, 12).flatMap(item => item.ledger.slice(-1).map(entry => <span key={`${item.id}-${entry.action}`}><b>{item.id} · {entry.action.replace(/_/g, ' ')}</b><small>{entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}</small></span>))}</div></section></>
}
function Exceptions({ cases, onVerify }: { cases: Case[]; onVerify: (id: string) => void }) {
  const pending = cases.filter(item => item.status === 'In review')
  return <><Title eyebrow="HUMAN-IN-THE-LOOP" title="Exceptions & verification" desc="Review the full decision context before confirming an outcome."/><div className="exception-banner"><AlertTriangle size={22}/><div><b>{pending.length} case{pending.length === 1 ? '' : 's'} requires attention</b><small>Verification is recorded in the audit trail and updates portfolio metrics.</small></div></div><section className="review-list"><div className="review-list-head"><span>OPEN REVIEW QUEUE</span><b>{pending.length} pending</b></div>{pending.length ? pending.map(item => <article className="review-card" key={item.id}><div className="review-card-top"><div><code>{item.id}</code><h2>{item.customer} <span>· {item.merchant}</span></h2><p>{item.failureDescription || item.reason}</p></div><span className="status in-review"><i/>Needs verification</span></div><div className="review-grid"><div><small>AT RISK</small><b>{money(item.amount)}</b></div><div><small>AI CONFIDENCE</small><b>{Math.round(item.probability * 100)}%</b></div><div><small>ATTEMPTS</small><b>{item.attempts}</b></div><div><small>EXPECTED VALUE</small><b>{money(item.netExpected)}</b></div></div><div className="review-columns"><div><small>WHY THIS WAS ESCALATED</small><p>{item.explanation || 'No action had a positive expected net value, so the case was routed for human review.'}</p><small>DIAGNOSIS</small><p>{item.reason}{item.failureCode ? ` · ${item.failureCode}` : ''}</p><small>RECOVERY ECONOMICS</small><p>Expected gross {money(item.expectedGross)} · Channel cost {money(item.channelCost)} · Net expected {money(item.netExpected)}</p></div><div><small>CONTACT HISTORY</small>{(item.communications || []).length ? item.communications.map((communication, index) => <p key={index}><b>{communication.channel === 'text' ? 'Text nudge' : 'Voice call'}</b>: {communication.message || communication.transcript || communication.status}</p>) : <p>No customer contact was made.</p>}<small>AUDIT TIMELINE</small><div className="audit-timeline">{(item.ledger || []).slice(-8).map((entry, index) => <span key={`${entry.action}-${index}`}><b>{entry.action.replace(/_/g, ' ')}</b><small>{entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''}</small></span>)}</div></div></div><div className="review-actions"><span>Verify only after checking your payment gateway or merchant ledger.</span><button className="verify" onClick={() => onVerify(item.id)}><Check size={13}/> Verify outcome</button></div></article>) : <div className="review-empty"><Check size={20}/><b>No cases require verification.</b><span>The queue is clear.</span></div>}</section></>
}
function Experiments({ results, onRun }: { results: Record<string, ExperimentMetrics> | null; onRun: () => void }) {
  const names: Record<string, string> = { silent_retry_only: 'Silent retry only', ladder: 'Full recovery ladder', contact_first: 'Contact first' }
  const rows = results ? Object.entries(results) : []
  const winner = rows.length ? rows.reduce((best, current) => current[1].net_recovered_paise > best[1].net_recovered_paise ? current : best) : null
  return <><Title eyebrow="STRATEGY LAB" title="Recovery experiments" desc="Compare all recovery strategies on the same five-event sample." action={<button className="primary" onClick={onRun}><Play size={15} fill="currentColor"/> Run experiment</button>}/>{winner && <section className="experiment-winner card"><small>RECOMMENDED STRATEGY</small><h2>{names[winner[0]]}</h2><p>Highest net recovered value in the latest deterministic run.</p><b>{money(winner[1].net_recovered_paise / 100)} net recovered</b></section>}<section className="card table-card"><div className="head"><div><small>STRATEGY COMPARISON</small><h2>{results ? 'Latest experiment results' : 'Run an experiment to compare strategies'}</h2></div></div>{rows.length ? <div className="table-wrap"><table><thead><tr><th>Strategy</th><th>Gross recovered</th><th>Net recovered</th><th>Recovered events</th><th>Contact cost</th><th>Human review</th></tr></thead><tbody>{rows.map(([key, value]) => <tr key={key}><td><b>{names[key] || key}</b>{winner?.[0] === key && <small className="winner-label">Winner</small>}</td><td>{money(value.gross_recovered_paise / 100)}</td><td><b>{money(value.net_recovered_paise / 100)}</b></td><td>{value.events_recovered}/{value.total_events}</td><td>{money(value.contact_cost_inr)}</td><td>{value.events_needs_human}</td></tr>)}</tbody></table></div> : <div className="experiment-empty"><Target size={24}/><p>Click “Run experiment” to execute silent retry, full ladder, and contact-first comparisons.</p></div>}</section></>
}
function Policy({ notify }: { notify: (message: string) => void }) {
  const [policy, setPolicy] = useState<PolicyData | null>(null)
  const [draft, setDraft] = useState<PolicyData | null>(null)
  useEffect(() => { getPolicy().then(value => { setPolicy(value); setDraft(value) }).catch(() => notify('Could not load policy settings.')) }, [])
  if (!draft) return <><Title eyebrow="GUARDRAILS" title="Policy center" desc="Merchant-approved automation boundaries."/><section className="card"><p>Loading live policy settings...</p></section></>
  const set = (key: keyof PolicyData, value: number) => setDraft(current => current ? { ...current, [key]: value } : current)
  const save = async () => { try { const updated = await updatePolicy({ max_silent_retries: draft.max_silent_retries, max_customer_contacts: draft.max_customer_contacts, voice_min_amount_paise: draft.voice_min_amount_paise, high_value_review_paise: draft.high_value_review_paise }); setPolicy(updated); setDraft(updated); notify('Policy saved and applied to new recovery runs.') } catch { notify('Policy could not be saved.') } }
  return <><Title eyebrow="GUARDRAILS" title="Policy center" desc="Configure the boundaries that keep recovery safe." action={<button className="primary" onClick={save}><Check size={15}/> Save policy</button>}/><div className="policy-layout"><section className="card policy-card"><div className="head"><div><small>RECOVERY LIMITS</small><h2>Automation boundaries</h2></div></div><label>Maximum silent retries <b>{draft.max_silent_retries}</b><input type="range" min="0" max="2" value={draft.max_silent_retries} onChange={event => set('max_silent_retries', Number(event.target.value))}/><small>System maximum: 2</small></label><label>Maximum customer contacts <b>{draft.max_customer_contacts}</b><input type="range" min="0" max="2" value={draft.max_customer_contacts} onChange={event => set('max_customer_contacts', Number(event.target.value))}/><small>Controls SMS/WhatsApp and voice attempts</small></label><label>Voice call minimum amount <b>{money(draft.voice_min_amount_paise / 100)}</b><input type="range" min="50000" max="500000" step="25000" value={draft.voice_min_amount_paise} onChange={event => set('voice_min_amount_paise', Number(event.target.value))}/><small>Voice is only considered above this amount</small></label><label>Human review threshold <b>{money(draft.high_value_review_paise / 100)}</b><input type="range" min="100000" max="10000000" step="100000" value={draft.high_value_review_paise} onChange={event => set('high_value_review_paise', Number(event.target.value))}/><small>High-value events are always routed to a human</small></label></section></div></>
}
