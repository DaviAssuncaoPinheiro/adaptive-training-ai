import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  Dumbbell,
  FlaskConical,
  Gauge,
  LockKeyhole,
  Play,
  ShieldCheck,
  Sparkles,
  TimerReset,
  TrendingUp,
} from 'lucide-react';
import Brand from '@/components/brand/Brand';
import styles from './page.module.css';

const signalItems = [
  'Check-in 07:10',
  'Readiness 82/100',
  'RPE medio 7.4',
  'PubMed match',
  'Deload detectado',
  'Microciclo V2',
  'Carga ajustada',
  'Tecnica preservada',
];

const outcomes = [
  {
    value: '4x',
    label: 'mais rapido para fechar um microciclo consistente',
  },
  {
    value: '24h',
    label: 'de memoria atletica viva entre sessao e planejamento',
  },
  {
    value: '100%',
    label: 'orientado por sinais, restricoes e evidencia atual',
  },
];

const engineSteps = [
  {
    title: 'Captura o estado real',
    body: 'Sono, energia, dor muscular, estresse, fadiga, historico de carga e RPE entram como sinais vivos.',
    Icon: Activity,
  },
  {
    title: 'Reprograma sem improviso',
    body: 'O sistema ajusta volume, intensidade e foco tecnico com limites claros para progressao, manutencao ou deload.',
    Icon: BrainCircuit,
  },
  {
    title: 'Explica com ciencia',
    body: 'Cada decisao pode ser justificada por referencias e raciocinio treinavel, nao por uma caixa-preta bonita.',
    Icon: FlaskConical,
  },
];

const workflow = [
  {
    label: '01',
    title: 'Check-in',
    body: 'O atleta registra prontidao em segundos.',
  },
  {
    label: '02',
    title: 'Sessao',
    body: 'Series, carga e RPE atualizam a memoria.',
  },
  {
    label: '03',
    title: 'Motor IA',
    body: 'O plano e recalculado com contexto e evidencias.',
  },
  {
    label: '04',
    title: 'Microciclo',
    body: 'A semana sai com progressao, cautela e justificativa.',
  },
];

const trustSignals = [
  { text: 'Supabase Auth + RLS', Icon: LockKeyhole },
  { text: 'FastAPI BFF-ready', Icon: ShieldCheck },
  { text: 'RAG cientifico', Icon: FlaskConical },
  { text: 'Treino adaptativo', Icon: Dumbbell },
];

export default function Home() {
  return (
    <main className={styles.landingPage}>
      <section className={styles.hero} aria-labelledby="hero-title">
        <div className={styles.heroVeil} aria-hidden="true" />

        <header className={styles.topbar}>
          <Link href="/" className={styles.brandLink} aria-label="Adaptive Training AI">
            <Brand />
          </Link>

          <nav className={styles.navLinks} aria-label="Navegacao principal">
            <a href="#engine">Motor</a>
            <a href="#workflow">Fluxo</a>
            <a href="#access">Acesso</a>
          </nav>

          <div className={styles.navActions}>
            <Link href="/login" className={styles.loginLink}>
              Login
            </Link>
            <Link href="/register" className={styles.navCta}>
              <span>Entrar na beta</span>
              <ArrowRight aria-hidden="true" size={16} strokeWidth={1.8} />
            </Link>
          </div>
        </header>

        <div className={styles.heroInner}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>SaaS para prescricao adaptativa de treino</p>
            <h1 id="hero-title">
              <span>Adaptive</span> <span>Training AI</span>
            </h1>
            <p className={styles.heroLead}>
              Um sistema operacional para transformar check-ins, carga, RPE e
              evidencia cientifica em microciclos que se ajustam antes do atleta
              quebrar.
            </p>

            <div className={styles.heroActions}>
              <Link href="/register" className={styles.primaryCta}>
                <Play aria-hidden="true" size={18} fill="currentColor" strokeWidth={1.5} />
                <span>Comecar agora</span>
              </Link>
              <Link href="/login" className={styles.secondaryCta}>
                <Gauge aria-hidden="true" size={18} strokeWidth={1.7} />
                <span>Ver dashboard</span>
              </Link>
            </div>

            <div className={styles.heroMeta} aria-label="Destaques da plataforma">
              {trustSignals.map(({ text, Icon }) => (
                <span key={text}>
                  <Icon aria-hidden="true" size={15} strokeWidth={1.7} />
                  {text}
                </span>
              ))}
            </div>
          </div>

          <aside className={styles.commandDeck} aria-label="Previa do motor adaptativo">
            <div className={styles.deckHeader}>
              <span>Live training state</span>
              <strong>82</strong>
            </div>
            <div className={styles.readinessRing} aria-hidden="true">
              <span>Readiness</span>
              <strong>82%</strong>
            </div>
            <div className={styles.signalGrid}>
              <span>Sleep</span>
              <strong>8.4</strong>
              <span>Stress</span>
              <strong>2.1</strong>
              <span>RPE cap</span>
              <strong>8.0</strong>
            </div>
            <div className={styles.waveRows} aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className={styles.microcycleChip}>
              <CalendarDays aria-hidden="true" size={16} strokeWidth={1.7} />
              Proximo bloco: hipertrofia tecnica
            </div>
          </aside>
        </div>
      </section>

      <section className={styles.signalRail} aria-label="Sinais processados">
        <div className={styles.signalTrack}>
          {[...signalItems, ...signalItems].map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </section>

      <section className={styles.outcomeSection}>
        <div className={styles.sectionIntro}>
          <p className={styles.eyebrow}>Performance intelligence</p>
          <h2>Um produto serio para quem programa treino de verdade.</h2>
          <p>
            Menos planilha quebrada, menos achismo, menos ajuste tardio. O
            Adaptive Training AI cria uma ponte entre rotina do atleta,
            resposta fisiologica e decisao pratica.
          </p>
        </div>

        <div className={styles.outcomeGrid}>
          {outcomes.map((item) => (
            <article className={styles.outcomeCard} key={item.value}>
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.engineSection} id="engine">
        <div className={styles.engineHeader}>
          <div>
            <p className={styles.eyebrow}>Motor adaptativo</p>
            <h2>O treino deixa de ser arquivo e vira sistema vivo.</h2>
          </div>
          <p>
            Cada bloco nasce com contexto: preferencia, restricao, historico,
            recuperacao e uma justificativa que o treinador consegue defender.
          </p>
        </div>

        <div className={styles.engineGrid}>
          {engineSteps.map(({ title, body, Icon }) => (
            <article className={styles.engineCard} key={title}>
              <Icon aria-hidden="true" size={22} strokeWidth={1.6} />
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.workflowSection} id="workflow">
        <div className={styles.workflowVisual} aria-hidden="true">
          <div className={styles.sessionPanel}>
            <div className={styles.sessionTop}>
              <span>Microcycle composer</span>
              <CheckCircle2 size={16} />
            </div>
            <div className={styles.sessionBars}>
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className={styles.sessionFooter}>
              <TimerReset size={16} />
              Ajuste em tempo real
            </div>
          </div>
        </div>

        <div className={styles.workflowCopy}>
          <p className={styles.eyebrow}>Fluxo operacional</p>
          <h2>Do sinal bruto ao microciclo pronto em uma linha clara.</h2>

          <div className={styles.timeline}>
            {workflow.map((item) => (
              <article className={styles.timelineItem} key={item.label}>
                <span>{item.label}</span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.accessSection} id="access">
        <div className={styles.accessCopy}>
          <Sparkles aria-hidden="true" size={28} strokeWidth={1.5} />
          <p className={styles.eyebrow}>Acesso antecipado</p>
          <h2>Coloque o motor para trabalhar no seu proximo bloco.</h2>
          <p>
            Cadastre-se, complete a anamnese, rode o primeiro check-in e deixe a
            plataforma construir um plano que responde ao atleta.
          </p>
        </div>

        <div className={styles.accessActions}>
          <Link href="/register" className={styles.primaryCta}>
            <TrendingUp aria-hidden="true" size={18} strokeWidth={1.7} />
            <span>Criar conta</span>
          </Link>
          <Link href="/login" className={styles.secondaryCta}>
            <Activity aria-hidden="true" size={18} strokeWidth={1.7} />
            <span>Ja tenho acesso</span>
          </Link>
        </div>
      </section>
    </main>
  );
}
