import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Beaker,
  BookOpen,
  ChevronDown,
  Database,
  Download,
  FileText,
  GitCommit,
  Info,
  ListChecks,
  Orbit,
  Radio,
  ShieldCheck,
  Sun,
} from 'lucide-react';

const TessHero = lazy(() => import('./TessHero.jsx'));

const warningCategories = [
  {
    key: 'background-comparison',
    title: 'Background comparison unavailable',
    description: 'A target-level correlation was skipped because the flagged and unflagged cadence groups did not both contain finite background measurements.',
    test: (warning) => warning.includes('background correlation skipped'),
    tone: 'caveat',
  },
  {
    key: 'underpowered-policy',
    title: 'Underpowered policy summary',
    description: 'The policy estimates are retained, but the target sample falls below the pre-declared minimum size for inference.',
    test: (warning) => warning.includes('below minimum_sample_size'),
    tone: 'caveat',
  },
];

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  useEffect(() => {
    let cancelled = false;
    fetch(path)
      .then((response) => {
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((error) => {
        if (!cancelled) setState({ data: null, error, loading: false });
      });
    return () => { cancelled = true; };
  }, [path]);
  return state;
}

function useNearViewport() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current || !('IntersectionObserver' in window)) {
      setVisible(true);
      return undefined;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '180px' },
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return [ref, visible];
}

function Section({ icon: Icon, code, title, className = '', dark = false, children }) {
  return (
    <article className={`${dark ? 'ops-panel-dark' : 'ops-panel'} ${className}`}>
      <div className="mb-6 flex items-center justify-between gap-4 border-b border-current/10 pb-4">
        <div className="flex items-center gap-3">
          <span className={`section-beacon ${dark ? 'section-beacon-dark' : ''}`}><Icon size={17} aria-hidden="true" /></span>
          <h2 className="text-xl font-bold uppercase tracking-[-0.02em]">{title}</h2>
        </div>
        {code && <span className="ops-code">{code}</span>}
      </div>
      {children}
    </article>
  );
}

function MetricLedger({ metrics }) {
  if (metrics.length === 0) {
    return <div className="telemetry-row"><p className="font-semibold">No results yet</p><p className="text-sm text-stone-500">Run scripts/run_analysis.py first.</p></div>;
  }
  return (
    <div className="telemetry-ledger">
      <div className="telemetry-head hidden md:grid">
        <span>Channel</span><span>Measurement</span><span>Estimate</span><span>Units</span><span>Sample</span>
      </div>
      {metrics.map((metric, index) => {
        const hasUncertainty = metric.uncertainty_low != null && metric.uncertainty_high != null;
        return (
          <article key={metric.name} className="telemetry-row">
            <span className="telemetry-channel">T{String(index + 1).padStart(2, '0')}</span>
            <div>
              <p className="break-words text-xs font-bold uppercase leading-5 tracking-[0.08em] text-stone-700">{metric.name.replace(/_/g, ' ')}</p>
              {hasUncertainty && <p className="mt-1 font-mono text-[0.66rem] text-orange-800">95% CI [{metric.uncertainty_low.toPrecision(3)}, {metric.uncertainty_high.toPrecision(3)}]</p>}
            </div>
            <p className="font-mono text-2xl font-semibold tabular-nums text-stone-950">{typeof metric.estimate === 'number' ? metric.estimate.toPrecision(4) : String(metric.estimate)}</p>
            <p className="text-xs text-stone-500">{metric.units}</p>
            <p className="font-mono text-xs text-stone-700">n={metric.sample_size}</p>
          </article>
        );
      })}
    </div>
  );
}

function inverseNormalCDF(p) {
  if (p <= 0 || p >= 1) return NaN;
  const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
  const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
  const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
  const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  let q;
  let r;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

function ConfidenceExplorer({ metrics }) {
  const withCI = (metrics || []).filter((metric) => metric.uncertainty_low != null && metric.uncertainty_high != null);
  const [selected, setSelected] = useState(null);
  const [confidence, setConfidence] = useState(95);

  useEffect(() => {
    if (!selected && withCI.length > 0) setSelected(withCI[0].name);
  }, [selected, withCI]);

  if (withCI.length === 0) return null;
  const metric = withCI.find((item) => item.name === selected) ?? withCI[0];
  const halfWidth95 = (metric.uncertainty_high - metric.uncertainty_low) / 2;
  const sigma = halfWidth95 / 1.959963984540054;
  const zLevel = inverseNormalCDF(0.5 + confidence / 200);
  const low = metric.estimate - zLevel * sigma;
  const high = metric.estimate + zLevel * sigma;

  return (
    <Section icon={Beaker} code="EXP-01" title="Confidence explorer">
      <p className="text-sm leading-6 text-stone-600">Approximate interval derived from the reported 95% bootstrap bounds under a normal sampling distribution. The recorded 95% interval remains the computed result.</p>
      {withCI.length > 1 && (
        <select className="mt-5 w-full border border-stone-300 bg-white px-3 py-2 text-sm" value={metric.name} onChange={(event) => setSelected(event.target.value)}>
          {withCI.map((item) => <option key={item.name} value={item.name}>{item.name.replace(/_/g, ' ')}</option>)}
        </select>
      )}
      <label className="mt-6 flex items-center justify-between text-sm"><span>Confidence level</span><span className="font-mono text-orange-700">{confidence.toFixed(1)}%</span></label>
      <input type="range" min="50" max="99.9" step="0.1" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} className="mt-3 w-full accent-orange-600" />
      <p className="mt-5 font-mono text-2xl font-semibold">[{low.toPrecision(4)}, {high.toPrecision(4)}]</p>
      <p className="mt-2 text-xs text-stone-500">{metric.units} · n={metric.sample_size}</p>
    </Section>
  );
}

function WarningAudit({ state }) {
  if (state.loading) return <p className="text-sm text-stone-400">Loading quality events…</p>;
  if (state.error) {
    return <div className="flex gap-3 border border-red-500 bg-red-950/40 p-4 text-sm text-red-100"><AlertCircle size={18} className="mt-0.5 shrink-0" />Could not load results/warnings.json: {String(state.error)}</div>;
  }
  const entries = Array.isArray(state.data) ? state.data : [];
  if (entries.length === 0) {
    return <div className="flex gap-3 border border-emerald-600 bg-emerald-950/30 p-4 text-sm text-emerald-100"><ShieldCheck size={18} className="mt-0.5 shrink-0" />No warnings recorded in results/warnings.json.</div>;
  }

  const claimed = new Set();
  const groups = warningCategories.map((category) => {
    const items = entries.filter((warning, index) => {
      if (claimed.has(index) || !category.test(warning)) return false;
      claimed.add(index);
      return true;
    });
    return { ...category, items };
  }).filter((group) => group.items.length > 0);
  const unclassified = entries.filter((_, index) => !claimed.has(index));
  if (unclassified.length > 0) {
    groups.push({ key: 'unclassified', title: 'Unclassified event', description: 'An event without a recognised display category; inspect its raw record below.', tone: 'failure', items: unclassified });
  }

  return (
    <div>
      <div className="mb-5 flex items-start gap-3 border border-orange-500/40 bg-orange-950/30 p-4">
        <Info size={18} className="mt-0.5 shrink-0 text-orange-300" aria-hidden="true" />
        <p className="text-sm leading-6 text-stone-200"><strong className="text-white">{entries.length} documented quality events.</strong> They record unavailable background comparisons and an underpowered target sample; none is a pipeline failure.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {groups.map((group) => (
          <div key={group.key} className={`warning-card warning-${group.tone}`}>
            <div className="flex items-start justify-between gap-4"><p className="font-bold uppercase tracking-wide text-white">{group.title}</p><span className="warning-count">{group.items.length}</span></div>
            <p className="mt-3 text-xs leading-5 text-stone-300">{group.description}</p>
          </div>
        ))}
      </div>
      <details className="raw-warning-list mt-4 border border-stone-700 bg-stone-950/50">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-4 text-sm font-semibold text-orange-200"><span>Show all {entries.length} raw entries</span><ChevronDown size={17} className="details-chevron" /></summary>
        <ol className="space-y-3 border-t border-stone-800 p-5 pl-10 text-xs leading-5 text-stone-300">
          {entries.map((warning, index) => <li key={`${index}-${warning}`} className="pl-1 marker:text-orange-400">{warning}</li>)}
        </ol>
      </details>
    </div>
  );
}

function LazyTessHero() {
  const [ref, visible] = useNearViewport();
  return (
    <div ref={ref} className="tess-hero-frame h-[23rem] overflow-hidden sm:h-[28rem] lg:h-full lg:min-h-[34rem]">
      {visible ? (
        <Suspense fallback={<div className="hero-loading grid h-full place-items-center text-xs uppercase tracking-[0.2em] text-orange-200">Loading observatory model…</div>}>
          <TessHero />
        </Suspense>
      ) : <div className="hero-loading h-full" aria-label="Observatory illustration placeholder" />}
    </div>
  );
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) return <main className="tess-page grid min-h-screen place-items-center text-xs uppercase tracking-[0.2em] text-orange-800">Loading mission audit…</main>;
  if (project.error || !project.data) return <main className="tess-page grid min-h-screen place-items-center text-red-800">Could not load project.json: {String(project.error)}</main>;

  const p = project.data;
  const metrics = summary.data?.metrics ?? [];
  const targetCount = metrics.reduce((largest, metric) => Math.max(largest, metric.sample_size || 0), 0);
  const isDemo = summary.data?.data_kind === 'synthetic_smoke_test' || summary.data?.data_kind === 'synthetic_demo';

  return (
    <main className="tess-page min-h-screen">
      <nav className="mission-nav">
        <div className="mx-auto flex max-w-[92rem] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3"><Sun size={18} className="text-orange-400" /><span className="text-xs font-bold uppercase tracking-[0.18em] text-stone-100">TESS photometry operations</span></div>
          <div className="flex items-center gap-4 font-mono text-[0.65rem] uppercase text-stone-400"><span>Sector 40</span><span>2-minute cadence</span><span>{targetCount || '—'} targets</span></div>
        </div>
      </nav>

      <header className="mx-auto max-w-[92rem] px-4 pt-5 sm:px-6 lg:px-8">
        <div className="mission-hero grid overflow-hidden lg:grid-cols-[1.05fr_0.95fr]">
          <div className="flex min-h-[31rem] flex-col justify-between p-6 sm:p-9 lg:p-12">
            <div>
              <p className="ops-code text-stone-900">{p.category}</p>
              <h1 className="mt-5 max-w-4xl text-5xl font-black uppercase leading-[0.92] tracking-[-0.055em] text-stone-950 sm:text-6xl xl:text-7xl">{p.title}</h1>
              <p className="mt-7 max-w-3xl text-lg font-medium leading-8 text-stone-800">{p.question}</p>
            </div>
            <div className="mt-10 flex flex-wrap gap-2 text-xs">
              <span className="mission-pill">{p.status}</span>
              <span className="mission-pill">Priority {p.priority}/10</span>
              <span className="mission-pill">{p.dataMode}</span>
              {summary.data && <span className={`mission-pill ${isDemo ? 'mission-pill-demo' : 'mission-pill-real'}`}>{isDemo ? 'Synthetic demo results' : 'Real data results'}</span>}
            </div>
          </div>
          <div className="border-t-4 border-stone-950 bg-stone-950 p-3 lg:border-l-4 lg:border-t-0"><LazyTessHero /></div>
        </div>
      </header>

      <div className="mx-auto max-w-[92rem] px-4 pb-14 sm:px-6 lg:px-8">
        {isDemo && <div className="mt-5 flex items-start gap-3 border-2 border-amber-500 bg-amber-100 p-4 text-sm leading-6 text-amber-950"><AlertTriangle size={18} className="mt-0.5 shrink-0" />These metrics and figures use clearly labelled synthetic demo data, not TESS observations.</div>}

        <section className="mt-12" aria-labelledby="telemetry-heading">
          <div className="mb-5 flex items-end justify-between gap-4"><div><p className="ops-code">TM / RESULT BUS</p><h2 id="telemetry-heading" className="mt-1 text-4xl font-black uppercase tracking-[-0.04em] text-stone-950">Telemetry ledger</h2></div><p className="hidden max-w-md text-right text-sm leading-6 text-stone-500 md:block">All aggregate channels from the real three-target audit, retained at their recorded precision.</p></div>
          <MetricLedger metrics={metrics} />
        </section>

        <section className="mt-12 grid gap-7 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="grid gap-7">
            <Section icon={ShieldCheck} code="PRV-01" title="Provenance boundary">
              <p className="text-sm leading-6 text-stone-700">{p.novelty}</p>
              <div className="mt-5 border-l-4 border-orange-500 bg-orange-50 p-4 text-sm leading-6 text-stone-800">No result is public-ready until validation and provenance checks pass.</div>
              {summary.data?.provenance && (
                <dl className="mt-5 space-y-3 text-xs">
                  <div className="flex items-center gap-2"><GitCommit size={14} className="text-orange-600" /><dt className="text-stone-500">git commit</dt><dd className="ml-auto font-mono text-stone-800">{summary.data.provenance.git_commit}</dd></div>
                  <div className="flex items-center gap-2"><FileText size={14} className="text-orange-600" /><dt className="text-stone-500">config sha256</dt><dd className="ml-auto max-w-[10rem] truncate font-mono text-stone-800">{summary.data.provenance.config_sha256 ?? 'n/a'}</dd></div>
                  <div className="flex items-center gap-2"><Beaker size={14} className="text-orange-600" /><dt className="text-stone-500">package version</dt><dd className="ml-auto font-mono text-stone-800">{summary.data.provenance.package_version}</dd></div>
                </dl>
              )}
            </Section>
            <ConfidenceExplorer metrics={metrics} />
          </div>
          <Section icon={ListChecks} code="VAL-05" title="Validation contract">
            <ol className="validation-stack">
              {p.validationContract.map((item, index) => <li key={item}><span>{String(index + 1).padStart(2, '0')}</span><p>{item}</p></li>)}
            </ol>
          </Section>
        </section>

        <section className="mt-12" aria-labelledby="figures-heading">
          <div className="mb-5"><p className="ops-code">IMG / DIAGNOSTIC DOWNLINK</p><h2 id="figures-heading" className="mt-1 text-4xl font-black uppercase tracking-[-0.04em] text-stone-950">Figure downlink</h2></div>
          <div className="figure-downlink">
            {p.figures.map((figure, index) => (
              <figure key={figure.id} className={`downlink-card downlink-card-${index + 1}`}>
                <div className="downlink-image"><img src={`./figures/${figure.id}.svg`} alt={figure.label} className="h-full w-full object-contain" loading={index > 1 ? 'lazy' : 'eager'} onError={(event) => { event.currentTarget.style.display = 'none'; }} /></div>
                <figcaption><span>{figure.label}</span><span className="font-mono text-[0.65rem] text-orange-700">FRAME {String(index + 1).padStart(2, '0')}</span></figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section className="mt-12">
          <Section icon={Radio} code="QEV-06" title="Quality event log" dark><WarningAudit state={warnings} /></Section>
        </section>

        <section className="mt-7 grid gap-7 lg:grid-cols-[1.15fr_0.85fr]">
          <Section icon={Orbit} code="MTH-01" title="Methodology" className="methodology-panel">
            <p className="text-sm leading-7 text-stone-700">{p.methodology}</p>
          </Section>
          <Section icon={BookOpen} code="BND-02" title="Assumptions and limitations">
            <p className="ops-code text-orange-700">Assumptions</p>
            <ul className="mt-3 space-y-3 text-sm leading-6 text-stone-700">{p.assumptions.map((item) => <li key={item} className="border-l-2 border-orange-400 pl-3">{item}</li>)}</ul>
            <p className="ops-code mt-7 text-red-700">Limitations</p>
            <ul className="mt-3 space-y-3 text-sm leading-6 text-stone-700">{p.limitations.map((item) => <li key={item} className="border-l-2 border-red-400 pl-3">{item}</li>)}</ul>
          </Section>
        </section>

        <footer className="mt-7 grid gap-7 lg:grid-cols-[1.2fr_0.8fr]">
          <Section icon={Download} code="DL-03" title="Downloads and provenance manifest">
            <div className="flex flex-wrap gap-2 text-sm"><a className="download-link" href="./manifest.csv" download>data/manifest.csv</a><a className="download-link" href="./results/summary.json" download>results/summary.json</a>{benchmarks.data && <a className="download-link" href="./results/benchmarks.json" download>results/benchmarks.json</a>}</div>
            <p className="mt-5 text-xs leading-5 text-stone-500">The manifest records product identifiers, source URLs, retrieval times, checksums, file sizes, selection reasons and archive terms.</p>
          </Section>
          <Section icon={Database} code="CIT-01" title="Citation and licence">
            <p className="text-sm text-stone-700">Author: {p.citation.author}</p><p className="mt-2 text-sm text-stone-700">Licence: {p.citation.license}</p><a className="mt-4 inline-block text-sm font-semibold text-orange-700 underline-offset-4 hover:underline" href={p.citation.repository}>{p.citation.repository}</a>
          </Section>
        </footer>
      </div>
    </main>
  );
}
