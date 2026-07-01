import React, { useState, useEffect, useRef } from 'react';

// Animated circular score ring — the signature element of this design.
// Fills from 0 to the match percentage when the results page mounts.
function ScoreRing({ score }) {
  const [displayed, setDisplayed] = useState(0);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayed / 100) * circumference;

  const color = score >= 70 ? '#4ADE80' : score >= 50 ? '#FBBF24' : '#F87171';

  useEffect(() => {
    let start = null;
    const duration = 1200;
    const animate = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplayed(Math.round(eased * score));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  return (
    <div className="score-ring-wrap">
      <svg className="score-ring-svg" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={radius} className="ring-track" />
        <circle
          cx="64" cy="64" r={radius}
          className="ring-fill"
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 64 64)"
        />
      </svg>
      <div className="score-ring-inner">
        <span className="score-number" style={{ color }}>{displayed}</span>
        <span className="score-pct">%</span>
        <span className="score-label">match</span>
      </div>
    </div>
  );
}

const TABS = ['Overview', 'Skills', 'Recommendations', 'Interview Q&A'];

function Results({ result, onNewAnalysis }) {
  const [activeTab, setActiveTab] = useState(0);
  const skillsWithQuestions = new Set(result.interview_questions.map((q) => q.skill));
  const skillsMissingCoverage = result.missing_skills.filter((s) => !skillsWithQuestions.has(s));

  return (
    <div className="results-page">
      {/* Sidebar */}
      <aside className="results-sidebar">
        <ScoreRing score={result.match_score} />

        <div className="sidebar-stats">
          <div className="sidebar-stat">
            <span className="stat-n green">{result.matched_skills.length}</span>
            <span className="stat-lbl">skills matched</span>
          </div>
          <div className="sidebar-stat">
            <span className="stat-n red">{result.missing_skills.length}</span>
            <span className="stat-lbl">gaps found</span>
          </div>
          <div className="sidebar-stat">
            <span className="stat-n purple">{result.interview_questions.length}</span>
            <span className="stat-lbl">practice questions</span>
          </div>
        </div>

        <button className="new-analysis-btn" onClick={onNewAnalysis}>
          ← New analysis
        </button>
      </aside>

      {/* Main content */}
      <div className="results-main">
        <div className="results-tabs">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              className={`results-tab ${activeTab === i ? 'active' : ''}`}
              onClick={() => setActiveTab(i)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="results-body">
          {/* Overview */}
          {activeTab === 0 && (
            <div className="tab-panel">
              <h2 className="panel-title">Your analysis summary</h2>
              <p className="panel-sub">
                {result.match_score >= 70
                  ? "Strong match. You're well-positioned for this role."
                  : result.match_score >= 50
                  ? "Decent match. A few skill gaps to close before applying."
                  : "Needs work. Significant skill gaps identified — use the plan below."}
              </p>
              <div className="overview-grid">
                <div className="overview-card green">
                  <div className="ov-n">{result.matched_skills.length}</div>
                  <div className="ov-label">Skills matched</div>
                  <div className="ov-chips">
                    {result.matched_skills.slice(0, 5).map((s, i) => (
                      <span key={i} className="chip green">{s}</span>
                    ))}
                    {result.matched_skills.length > 5 && (
                      <span className="chip ghost">+{result.matched_skills.length - 5} more</span>
                    )}
                  </div>
                </div>
                <div className="overview-card red">
                  <div className="ov-n">{result.missing_skills.length}</div>
                  <div className="ov-label">Skills to learn</div>
                  <div className="ov-chips">
                    {result.missing_skills.slice(0, 5).map((s, i) => (
                      <span key={i} className="chip red">{s}</span>
                    ))}
                    {result.missing_skills.length > 5 && (
                      <span className="chip ghost">+{result.missing_skills.length - 5} more</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Skills */}
          {activeTab === 1 && (
            <div className="tab-panel">
              <h2 className="panel-title">Skill breakdown</h2>
              <div className="skills-section">
                <div className="skills-heading green">
                  <span className="skills-dot green" /> Matched ({result.matched_skills.length})
                </div>
                <div className="chips-wrap">
                  {result.matched_skills.length > 0
                    ? result.matched_skills.map((s, i) => <span key={i} className="chip green">{s}</span>)
                    : <span className="empty-note">No matched skills</span>}
                </div>
              </div>
              <div className="skills-section">
                <div className="skills-heading red">
                  <span className="skills-dot red" /> Missing ({result.missing_skills.length})
                </div>
                <div className="chips-wrap">
                  {result.missing_skills.length > 0
                    ? result.missing_skills.map((s, i) => <span key={i} className="chip red">{s}</span>)
                    : <span className="empty-note">You have all required skills 🎉</span>}
                </div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {activeTab === 2 && (
            <div className="tab-panel">
              <h2 className="panel-title">Learning plan</h2>
              {result.recommended_topics.length > 0 ? (
                <div className="rec-list">
                  {result.recommended_topics.map((topic, i) => (
                    <div key={i} className={`rec-card priority-${topic.priority}`}>
                      <div className="rec-header">
                        <span className="rec-name">{topic.name}</span>
                        <span className={`priority-pill ${topic.priority}`}>{topic.priority}</span>
                      </div>
                      <ul className="rec-resources">
                        {topic.resources.map((r, j) => (
                          <li key={j}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-note">No recommendations at this time.</p>
              )}
            </div>
          )}

          {/* Interview Q&A */}
          {activeTab === 3 && (
            <div className="tab-panel">
              <h2 className="panel-title">Practice questions</h2>
              {result.interview_questions.length > 0 ? (
                <div className="q-list">
                  {result.interview_questions.map((q, i) => (
                    <div key={i} className="q-card">
                      <div className="q-meta">
                        <span className={`diff-pill ${q.difficulty}`}>{q.difficulty}</span>
                        <span className="q-topic">{q.topic}</span>
                      </div>
                      <p className="q-text">{q.question}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-note">No questions available yet.</p>
              )}
              {skillsMissingCoverage.length > 0 && (
                <div className="coverage-note">
                  <span className="cov-icon">ℹ</span>
                  <div>
                    <strong>No questions yet for: {skillsMissingCoverage.join(', ')}</strong>
                    <p>Run another analysis to generate questions for these skills — they're cached after the first run.</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Results;
