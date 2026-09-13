import type { Screen } from "../App";
import Logo from "./Logo";

interface Props { navigate: (s: Screen) => void; }

const features = [
  { icon: "◈", title: "AI Theme Detection", desc: "Automatically identify the issues customers discuss most." },
  { icon: "◉", title: "Sentiment Intelligence", desc: "Understand how customers feel across thousands of reviews." },
  { icon: "◇", title: "Evidence-Based Insights", desc: "Every insight is connected to real customer feedback." },
  { icon: "△", title: "Trend Detection", desc: "Identify problems before they become major product issues." },
];

export default function Landing({ navigate }: Props) {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg)" }}>
      {/* Nav */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 lg:px-10"
        style={{
          height: "60px",
          background: "rgba(9,9,11,0.8)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <Logo size={26} />
        <div className="hidden md:flex items-center gap-7 text-sm" style={{ color: "var(--fg3)" }}>
          {["Product", "Solutions", "Features", "Enterprise"].map((l) => (
            <button key={l} className="transition-colors hover:text-white" style={{ color: "inherit" }}>{l}</button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button className="text-sm hidden md:block transition-colors hover:text-white" style={{ color: "var(--fg3)" }}>Sign In</button>
          <button
            onClick={() => navigate("upload")}
            className="btn-primary px-4 py-2 rounded-xl text-sm"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center text-center pt-36 pb-12 px-6">
        {/* Badge */}
        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-8 border"
          style={{ background: "rgba(124,58,237,0.1)", borderColor: "rgba(124,58,237,0.3)", color: "var(--accent)" }}
        >
          <span className="w-1.5 h-1.5 rounded-full animate-pulse-ring" style={{ background: "var(--accent)" }} />
          AI-Powered Review Intelligence
        </div>

        <h1
          className="font-black tracking-tight mb-5 leading-[1.07]"
          style={{ fontSize: "clamp(2.4rem, 6vw, 4.2rem)", color: "var(--fg)", maxWidth: "820px" }}
        >
          Turn Thousands of Reviews Into{" "}
          <span className="gradient-text">Product Decisions.</span>
        </h1>

        <p className="mb-10 leading-relaxed" style={{ color: "var(--fg2)", fontSize: "1.1rem", maxWidth: "540px" }}>
          InsightAI automatically analyzes customer feedback, detects emerging problems, understands sentiment, and reveals what your customers actually care about.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-3 mb-24">
          <button
            onClick={() => navigate("upload")}
            className="btn-primary px-7 py-3 rounded-xl text-sm flex items-center gap-2"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            Analyze Reviews
          </button>
          <button
            onClick={() => navigate("dashboard")}
            className="btn-ghost px-7 py-3 rounded-xl text-sm flex items-center gap-2"
          >
            Watch Demo
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>
            </svg>
          </button>
        </div>

        {/* Dashboard preview */}
        <div className="relative w-full max-w-5xl mx-auto animate-float">
          {/* Glow */}
          <div
            className="absolute inset-x-16 -top-8 h-20 blur-3xl opacity-30 pointer-events-none"
            style={{ background: "var(--gradient)" }}
          />
          <div
            className="rounded-2xl overflow-hidden border"
            style={{ background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05)" }}
          >
            {/* Browser chrome */}
            <div className="flex items-center gap-2 px-4 h-10 border-b" style={{ background: "var(--bg2)", borderColor: "var(--border)" }}>
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#ef4444" }} />
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#f59e0b" }} />
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#10b981" }} />
              <div className="flex-1 mx-4 h-5 rounded flex items-center px-3 text-xs" style={{ background: "rgba(255,255,255,0.04)", color: "var(--fg3)" }}>
                app.insightai.com/dashboard
              </div>
            </div>
            {/* Mini dashboard */}
            <div className="flex">
              {/* Sidebar preview */}
              <div className="hidden md:flex flex-col gap-1 w-40 p-3 border-r" style={{ borderColor: "var(--border)", background: "var(--bg2)" }}>
                {["Dashboard", "Analyze", "Themes", "Explorer", "Trends"].map((item, i) => (
                  <div key={item}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
                    style={i === 0
                      ? { background: "var(--gradient-soft)", color: "var(--fg)", borderLeft: "1px solid rgba(124,58,237,0.4)" }
                      : { color: "var(--fg3)" }
                    }
                  >
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: i === 0 ? "var(--accent)" : "var(--border)" }} />
                    {item}
                  </div>
                ))}
              </div>
              {/* Main area */}
              <div className="flex-1 p-5 space-y-4">
                {/* AI Banner */}
                <div className="rounded-xl p-4 border" style={{ background: "var(--gradient-soft)", borderColor: "rgba(124,58,237,0.25)" }}>
                  <div className="text-xs font-semibold mb-1" style={{ color: "var(--accent)" }}>AI INSIGHT</div>
                  <div className="text-xs" style={{ color: "var(--fg2)" }}>Negative sentiment has increased around payment reliability and app stability.</div>
                </div>
                {/* Metric cards */}
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { l: "Total Reviews", v: "10,000", c: "var(--fg)" },
                    { l: "Positive", v: "65%", c: "var(--positive)" },
                    { l: "Neutral", v: "20%", c: "var(--neutral-s)" },
                    { l: "Negative", v: "15%", c: "var(--negative)" },
                  ].map(({ l, v, c }) => (
                    <div key={l} className="rounded-xl p-3 border" style={{ background: "var(--card2)", borderColor: "var(--border)" }}>
                      <div className="text-base font-extrabold" style={{ color: c }}>{v}</div>
                      <div className="text-xs mt-0.5" style={{ color: "var(--fg3)" }}>{l}</div>
                    </div>
                  ))}
                </div>
                {/* Theme cards */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { n: "App Crashes", m: "245", s: "negative" },
                    { n: "Slow Performance", m: "180", s: "negative" },
                    { n: "Easy to Use", m: "340", s: "positive" },
                  ].map(({ n, m, s }) => (
                    <div key={n} className="rounded-xl p-3 border" style={{ background: "var(--card2)", borderColor: "var(--border)" }}>
                      <div className="text-xs font-semibold mb-1" style={{ color: "var(--fg)" }}>{n}</div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs" style={{ color: "var(--fg3)" }}>{m}</span>
                        <span className="text-xs px-1.5 py-0.5 rounded-full" style={{
                          background: s === "positive" ? "var(--positive-bg)" : "var(--negative-bg)",
                          color: s === "positive" ? "var(--positive)" : "var(--negative)",
                        }}>{s}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-28 px-6 max-w-5xl mx-auto w-full">
        <div className="text-center mb-16">
          <div className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-4 border" style={{ background: "rgba(99,102,241,0.08)", borderColor: "rgba(99,102,241,0.2)", color: "var(--accent)" }}>
            CAPABILITIES
          </div>
          <h2 className="font-bold mb-3" style={{ fontSize: "1.9rem", color: "var(--fg)" }}>
            Everything your team needs to<br />understand customer feedback
          </h2>
          <p style={{ color: "var(--fg2)" }}>Powered by advanced AI. Designed for product teams.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map(({ icon, title, desc }) => (
            <div
              key={title}
              className="card-hover rounded-2xl border p-6 cursor-default group relative overflow-hidden"
              style={{ background: "var(--card)", borderColor: "var(--border)" }}
            >
              {/* Gradient hover highlight */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                style={{ background: "radial-gradient(circle at 30% 20%, rgba(124,58,237,0.07), transparent 70%)" }} />
              <div className="text-2xl mb-4" style={{ color: "var(--accent)" }}>{icon}</div>
              <h3 className="font-semibold text-sm mb-2" style={{ color: "var(--fg)" }}>{title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--fg3)" }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 px-6 border-t text-center text-xs" style={{ borderColor: "var(--border)", color: "var(--fg3)" }}>
        <div className="flex items-center justify-center gap-2 mb-2">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          Privacy Protected · SOC 2 Compliant · GDPR Ready
        </div>
        © 2026 InsightAI. All rights reserved.
      </footer>
    </div>
  );
}
