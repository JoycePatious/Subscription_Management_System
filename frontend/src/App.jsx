import React, { useState } from 'react'
import { LayoutDashboard, Users, Package, Repeat, FileText, CreditCard, Tags, BarChart3, Settings, Search, Bell, CircleHelp, Menu, ArrowUpRight, Clock3, CheckCircle2, Wallet } from 'lucide-react'

const nav = [
  ['Overview', LayoutDashboard], ['Customers', Users], ['Products & Variants', Package],
  ['Plans', Tags], ['Quotations', FileText], ['Subscriptions', Repeat],
  ['Invoices', FileText], ['Payments', CreditCard], ['Discounts & Taxes', Settings],
  ['Reports', BarChart3], ['Customer Portal', Wallet]
]
const sampleRows = {
  'Customers': [['Northstar Retail','northstar@example.com','Business','Active'],['Pixel Works','hello@pixelworks.in','Business','Active'],['Green Basket','accounts@greenbasket.in','Business','Pending']],
  'Products & Variants': [['Business Suite','Software','₹1,000','2 variants'],['Cloud Backup','Add-on','₹300','1 variant'],['Analytics Pro','Software','₹2,500','No variants']],
  'Plans': [['Basic Monthly','Monthly','₹500','Active'],['Pro Monthly','Monthly','₹1,200','Active'],['Enterprise Annual','Yearly','₹10,000','Active']],
  'Quotations': [['QT-2026-001','Northstar Retail','₹12,000','Sent'],['QT-2026-002','Pixel Works','₹5,000','Draft']],
  'Subscriptions': [['SUB-001','Northstar Retail','Pro Monthly','Active'],['SUB-002','Pixel Works','Basic Monthly','Active'],['SUB-003','Green Basket','Enterprise Annual','Paused']],
  'Invoices': [['INV-001','Northstar Retail','₹1,200','Confirmed'],['INV-002','Pixel Works','₹500','Paid'],['INV-003','Green Basket','₹10,000','Overdue']],
  'Payments': [['PAY-001','INV-002','₹500','UPI'],['PAY-002','INV-001','₹600','Bank transfer']],
  'Discounts & Taxes': [['WELCOME10','Percentage','10%','Active'],['BULK100','Fixed','₹100','Active'],['GST Sample','Tax','18%','Active']]
}
function App() {
  const [active,setActive] = useState('Overview')
  const [role,setRole] = useState('Admin')
  const [query,setQuery] = useState('')
  const [mobile,setMobile] = useState(false)
  const rows = sampleRows[active] || []
  const cards = [
    ['Active subscriptions','1,284','+8.2% this month',Repeat],
    ['Payments received','₹8,42,500','This month',Wallet],
    ['Outstanding','₹1,24,800','Across open invoices',Clock3],
    ['Overdue invoices','18','Needs attention',FileText]
  ]
  return <div className="app-shell">
    <aside className={`sidebar ${mobile?'show':''}`}>
      <div className="brand"><div className="brand-mark">B</div><div><b>brightloop</b><small>SUBSCRIPTION SUITE</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{nav.map(([name,Icon])=><button key={name} className={`nav-item ${active===name?'selected':''}`} onClick={()=>{setActive(name);setMobile(false)}}><Icon size={17}/><span>{name}</span>{name==='Invoices'&&<i>3</i>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="help-card"><CircleHelp size={18}/><b>Need a hand?</b><p>Explore the workspace and build your workflow.</p></div><div className="profile"><div className="avatar">JT</div><div><b>Workspace User</b><small>{role} account</small></div><Settings size={17}/></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="mobile-menu" onClick={()=>setMobile(!mobile)}><Menu/></button><div className="crumb">Workspace <span>/</span> <b>{active}</b></div><div className="top-actions"><div className="role-switch"><span>View as</span><select value={role} onChange={e=>setRole(e.target.value)}><option>Admin</option><option>Staff</option><option>Customer</option></select></div><button className="icon-btn"><Bell size={18}/><em/></button><div className="avatar">JT</div></div></header>
      <section className="content">
        <div className="page-heading"><div><div className="eyebrow">BRIGHTLOOP SOFTWARE</div><h1>{active==='Overview'?'Good morning, Jesbel':active}</h1><p>{active==='Overview'?'Here’s what’s happening with your subscriptions today.':`Manage and keep track of your ${active.toLowerCase()} in one place.`}</p></div><button className="primary" onClick={()=>alert('Connect this action to the relevant create API/form.')}>＋ Create new</button></div>
        {active==='Overview'?<>
          <div className="metric-grid">{cards.map(([label,value,sub,Icon])=><article className="metric" key={label}><div className="metric-top"><span>{label}</span><Icon size={18}/></div><strong>{value}</strong><small>{sub}</small></article>)}</div>
          <div className="dashboard-grid"><article className="panel revenue"><div className="panel-head"><div><h3>Revenue overview</h3><p>Payments received over the last 6 months</p></div><select><option>Last 6 months</option><option>This year</option></select></div><div className="chart">{[42,58,48,75,62,90].map((v,i)=><div className="bar-wrap" key={i}><div className="bar" style={{height:`${v}%`}}/><small>{['May','Jun','Jul','Aug','Sep','Oct'][i]}</small></div>)}</div></article>
          <article className="panel"><div className="panel-head"><div><h3>Subscription health</h3><p>Current status breakdown</p></div><ArrowUpRight size={18}/></div><div className="health-number">1,284 <small>total subscriptions</small></div>{[['Active',78],['Paused',13],['Closed',9]].map(([n,v])=><div className="health-row" key={n}><div><span>{n}</span><b>{v}%</b></div><div className="track"><i style={{width:`${v}%`}}/></div></div>)}</article></div>
          <div className="panel"><div className="panel-head"><div><h3>Recent activity</h3><p>Latest updates across your workspace</p></div><button className="text-btn" onClick={()=>setActive('Subscriptions')}>View subscriptions →</button></div><div className="activity"><span className="activity-icon"><CheckCircle2/></span><div><b>Subscription activated</b><p>Northstar Retail · Pro Monthly</p></div><time>12 min ago</time></div><div className="activity"><span className="activity-icon gold"><CreditCard/></span><div><b>Payment recorded</b><p>Invoice INV-002 · ₹500</p></div><time>1 hour ago</time></div></div>
        </>:<div className="panel"><div className="table-toolbar"><div className="search"><Search size={16}/><input placeholder={`Search ${active.toLowerCase()}...`} value={query} onChange={e=>setQuery(e.target.value)}/></div><button className="outline">Filters</button><button className="outline">Export</button></div>{rows.length?<div className="table-scroll"><table><thead><tr>{rows[0].map((_,i)=><th key={i}>{(active==='Customers'?['CUSTOMER','EMAIL','TYPE','STATUS']:active==='Products & Variants'?['PRODUCT','TYPE','BASE PRICE','VARIANTS']:active==='Plans'?['PLAN','BILLING','PRICE','STATUS']:active==='Quotations'?['REFERENCE','CUSTOMER','TOTAL','STATUS']:active==='Subscriptions'?['REFERENCE','CUSTOMER','PLAN','STATUS']:active==='Invoices'?['INVOICE','CUSTOMER','TOTAL','STATUS']:active==='Payments'?['PAYMENT','INVOICE','AMOUNT','METHOD']:['NAME','TYPE','VALUE','STATUS'])[i]}</th>)}</tr></thead><tbody>{rows.filter(r=>r.join(' ').toLowerCase().includes(query.toLowerCase())).map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{j===3?<span className={`status ${v.toLowerCase()}`}>{v}</span>:v}</td>)}</tr>)}</tbody></table></div>:<div className="empty"><div className="empty-icon"><Package/></div><h3>Build your {active.toLowerCase()} workspace</h3><p>Your records will appear here once you connect the API and add data.</p><button className="primary" onClick={()=>alert('Build a create form and connect it to the backend endpoint.')}>＋ Add first record</button></div>}</div>}
        <footer>Brightloop Subscription Suite <span>Starter workspace · Connect API to replace demo data</span></footer>
      </section>
    </main>
  </div>
}
export default App
