export default function About() {
  return (
    <section aria-labelledby="about-heading">
      <h1 id="about-heading">About</h1>

      <div className="card">
        <h2>Network Traffic Anomaly Detector</h2>
        <p>Personal Research Project (PRP)</p>

        <ul>
          <li>Backend: FastAPI · scikit-learn</li>
          <li>Dataset: CICIDS2017 / synthetic CIC-flow features</li>
          <li>Algorithms: Random Forest, Gradient Boosting, Isolation Forest, One-Class SVM</li>
          <li>Frontend: React + TypeScript + Vite, charts via Plotly</li>
        </ul>

        <p>
          Built as part of the Cybersecurity <em>Attack &amp; Defend</em> minor at Fontys University of
          Applied Sciences. See <code>docs/research/DOT_Research.md</code> for the full research
          substantiation and <code>docs/evidence/</code> for per-LO evidence dossiers.
        </p>
      </div>
    </section>
  );
}
