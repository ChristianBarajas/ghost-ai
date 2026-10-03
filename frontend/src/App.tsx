import {
  useEffect,
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import "./App.css";

import {
  checkGhostHealth,
  getGhostSkills,
  getGhostTasks,
  runGhostAgent,
} from "./services/ghostApi";

import type {
  AgentRoute,
  GhostSkill,
  GhostTask,
  GhostTaskResult,
  ProjectVerification,
  ResearchResult,
} from "./types/ghost";


function isResearchResult(
  result: GhostTaskResult | null,
): result is ResearchResult {
  return (
    result !== null
    && "key_terms" in result
    && "summary" in result
  );
}


function isProjectVerification(
  result: GhostTaskResult | null,
): result is ProjectVerification {
  return (
    result !== null
    && "project" in result
    && "checks" in result
    && "summary" in result
  );
}


function App() {
  const [
    request,
    setRequest,
  ] = useState(
    "What is reinforcement learning?",
  );

  const [
    provider,
    setProvider,
  ] = useState(
    "duckduckgo",
  );

  const [
    task,
    setTask,
  ] = useState<GhostTask | null>(
    null,
  );

  const [
    route,
    setRoute,
  ] = useState<AgentRoute | null>(
    null,
  );

  const [
    taskHistory,
    setTaskHistory,
  ] = useState<GhostTask[]>([]);

  const [
    skills,
    setSkills,
  ] = useState<GhostSkill[]>([]);

  const [
    selectedSkill,
    setSelectedSkill,
  ] = useState<GhostSkill | null>(
    null,
  );

  const [
    isRunning,
    setIsRunning,
  ] = useState(false);

  const [
    backendOnline,
    setBackendOnline,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  async function loadTaskHistory() {
    try {
      const tasks =
        await getGhostTasks();

      setTaskHistory(tasks);
    } catch {
      // History should not block GHOST.
    }
  }


  async function loadSkills() {
    try {
      const learnedSkills =
        await getGhostSkills();

      setSkills(
        learnedSkills,
      );

      setSelectedSkill(
        learnedSkills.find(
          (skill) =>
            skill.name === "research_topic",
        )
        ?? learnedSkills[0]
        ?? null,
      );
    } catch {
      // Skills should not block GHOST.
    }
  }


  useEffect(() => {
    async function initializeGhost() {
      try {
        await checkGhostHealth();

        setBackendOnline(true);

        await Promise.all([
          loadTaskHistory(),
          loadSkills(),
        ]);
      } catch {
        setBackendOnline(false);
      }
    }

    initializeGhost();
  }, []);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanRequest =
      request.trim();

    if (!cleanRequest) {
      return;
    }

    setIsRunning(true);
    setTask(null);
    setRoute(null);
    setError(null);

    try {
      const response =
        await runGhostAgent({
          request: cleanRequest,
          provider,
        });

      setRoute(
        response.route,
      );

      setTask(
        response.task,
      );

      if (response.executed) {
        await loadTaskHistory();
      }

      const selected =
        skills.find(
          (skill) =>
            skill.name
            === response.route.skill,
        );

      if (selected) {
        setSelectedSkill(
          selected,
        );
      }
    } catch (requestError) {
      if (
        requestError
        instanceof Error
      ) {
        setError(
          requestError.message,
        );
      } else {
        setError(
          "Unknown GHOST error.",
        );
      }
    } finally {
      setIsRunning(false);
    }
  }


  function formatTaskDate(
    date: string | null,
  ) {
    if (!date) {
      return "Unknown time";
    }

    const parsedDate =
      new Date(
        date.replace(
          " ",
          "T",
        ) + "Z",
      );

    return parsedDate.toLocaleString();
  }


  function openHistoryTask(
    historyTask: GhostTask,
  ) {
    setTask(
      historyTask,
    );

    setRoute(null);
    setError(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }


  const researchResult =
    task
    && isResearchResult(
      task.result,
    )
      ? task.result
      : null;

  const projectResult =
    task
    && isProjectVerification(
      task.result,
    )
      ? task.result
      : null;


  return (
    <main className="app-shell">
      <section className="hero">
        <div className="top-bar">
          <div className="brand">
            <div className="ghost-mark">
              👻
            </div>

            <div>
              <h1>
                GHOST
              </h1>

              <p className="brand-subtitle">
                Self-Programming Personal Software
              </p>
            </div>
          </div>

          <div
            className={
              backendOnline
                ? "status online"
                : "status offline"
            }
          >
            <span className="status-dot" />

            {backendOnline
              ? "Backend Online"
              : "Backend Offline"}
          </div>
        </div>

        <div className="hero-copy">
          <p className="eyebrow">
            AI WORKFLOW AGENT
          </p>

          <h2>
            What do you want GHOST to do?
          </h2>

          <p>
            Describe the task naturally.
            GHOST will choose the appropriate
            skill, extract its inputs, execute
            the workflow, verify the result,
            and remember the run.
          </p>
        </div>

        <form
          className="task-form"
          onSubmit={handleSubmit}
        >
          <label htmlFor="ghost-request">
            Give GHOST a task
          </label>

          <textarea
            id="ghost-request"
            value={request}
            onChange={(event) =>
              setRequest(
                event.target.value,
              )
            }
            placeholder="Try: Check if ~/Desktop/ghost is healthy"
            rows={4}
          />

          <div className="form-footer">
            <div className="provider-control">
              <label htmlFor="provider">
                Web provider
              </label>

              <select
                id="provider"
                value={provider}
                onChange={(event) =>
                  setProvider(
                    event.target.value,
                  )
                }
              >
                <option value="duckduckgo">
                  DuckDuckGo
                </option>

                <option value="bing">
                  Bing
                </option>
              </select>
            </div>

            <button
              type="submit"
              disabled={
                isRunning
                || !backendOnline
              }
            >
              {isRunning
                ? "GHOST is thinking..."
                : "Run GHOST"}
            </button>
          </div>
        </form>
      </section>


      {isRunning && (
        <section className="panel execution-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                AGENT EXECUTION
              </p>

              <h3>
                GHOST is working
              </h3>
            </div>

            <div className="spinner" />
          </div>

          <div className="execution-list">
            <div className="execution-step active">
              <span>
                01
              </span>

              <p>
                Understanding your request...
              </p>
            </div>

            <div className="execution-step">
              <span>
                02
              </span>

              <p>
                Selecting the best skill...
              </p>
            </div>

            <div className="execution-step">
              <span>
                03
              </span>

              <p>
                Executing and verifying...
              </p>
            </div>
          </div>
        </section>
      )}


      {error && (
        <section className="panel error-panel">
          <p className="eyebrow">
            ERROR
          </p>

          <h3>
            GHOST could not complete the task.
          </h3>

          <p>
            {error}
          </p>
        </section>
      )}


      {route && (
        <section className="panel result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                AI ROUTING
              </p>

              <h3>
                {route.skill}
              </h3>
            </div>

            <div className="result-badge success">
              {Math.round(
                route.confidence * 100,
              )}
              % confidence
            </div>
          </div>

          <div className="result-meta">
            <span>
              Skill:{" "}
              {route.skill}
            </span>

            <span>
              Inputs:{" "}
              {
                Object.keys(
                  route.variables,
                ).length
              }
            </span>
          </div>

          <div className="summary-card">
            <p className="summary">
              {route.reason}
            </p>
          </div>

          {route.missing_variables.length
            > 0 && (
            <div className="error-panel">
              <p className="eyebrow">
                INPUT REQUIRED
              </p>

              <h3>
                GHOST understands the task,
                but needs more information.
              </h3>

              <p>
                Missing:{" "}
                {route.missing_variables.join(
                  ", ",
                )}
              </p>
            </div>
          )}
        </section>
      )}


      {task && researchResult && (
        <section className="panel result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                RESEARCH RESULT
              </p>

              <h3>
                {researchResult.title
                  ?? task.query}
              </h3>
            </div>

            <div
              className={
                task.success
                  ? "result-badge success"
                  : "result-badge failure"
              }
            >
              {task.success
                ? "Verified"
                : "Failed"}
            </div>
          </div>

          <div className="result-meta">
            <span>
              Skill:{" "}
              {task.skill ?? "Unknown"}
            </span>

            <span>
              Provider:{" "}
              {task.provider}
            </span>

            <span>
              Task:{" "}
              #{task.task_id}
            </span>
          </div>

          <div className="summary-card">
            <p className="summary">
              {researchResult.summary}
            </p>
          </div>

          <div className="terms">
            {researchResult.key_terms.map(
              (term) => (
                <span
                  key={term}
                  className="term"
                >
                  {term}
                </span>
              ),
            )}
          </div>

          {researchResult.url && (
            <a
              className="source-link"
              href={researchResult.url}
              target="_blank"
              rel="noreferrer"
            >
              View source
              {" → "}
              {researchResult.domain}
            </a>
          )}
        </section>
      )}


      {task && projectResult && (
        <section className="panel project-result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                PROJECT VERIFICATION
              </p>

              <h3>
                {
                  projectResult
                    .project.project_path
                }
              </h3>
            </div>

            <div
              className={
                task.verified
                  ? "result-badge success"
                  : "result-badge failure"
              }
            >
              {task.verified
                ? "Verified"
                : "Failed"}
            </div>
          </div>

          <div className="result-meta">
            <span>
              Skill:{" "}
              {task.skill ?? "Unknown"}
            </span>

            <span>
              Provider:{" "}
              {task.provider}
            </span>

            <span>
              Task:{" "}
              #{task.task_id}
            </span>
          </div>

          <div className="verification-stats">
            <div>
              <strong>
                {
                  projectResult
                    .summary.total_checks
                }
              </strong>

              <span>
                Checks
              </span>
            </div>

            <div>
              <strong>
                {
                  projectResult
                    .summary.passed
                }
              </strong>

              <span>
                Passed
              </span>
            </div>

            <div>
              <strong>
                {
                  projectResult
                    .summary.failed
                }
              </strong>

              <span>
                Failed
              </span>
            </div>
          </div>

          <div className="detected-stack">
            <p className="skill-section-title">
              Detected Stack
            </p>

            <div className="terms">
              {
                projectResult
                  .project.project_types.map(
                    (type) => (
                      <span
                        key={type}
                        className="term"
                      >
                        {type}
                      </span>
                    ),
                  )
              }
            </div>
          </div>

          <div className="project-checks">
            <p className="skill-section-title">
              Verification Checks
            </p>

            {
              projectResult.checks.map(
                (check) => (
                  <div
                    key={`${check.component}-${check.name}`}
                    className="project-check"
                  >
                    <span
                      className={
                        check.success
                          ? "check-icon passed"
                          : "check-icon failed"
                      }
                    >
                      {check.success
                        ? "✓"
                        : "×"}
                    </span>

                    <div>
                      <strong>
                        {check.name}
                      </strong>

                      <p>
                        {check.component}
                        {" · "}
                        {check.command.join(
                          " ",
                        )}
                      </p>
                    </div>

                    <span
                      className={
                        check.success
                          ? "check-status passed"
                          : "check-status failed"
                      }
                    >
                      {check.success
                        ? "PASS"
                        : "FAIL"}
                    </span>
                  </div>
                ),
              )
            }
          </div>
        </section>
      )}


      {task && !task.result && (
        <section className="panel error-panel">
          <p className="eyebrow">
            EXECUTION RESULT
          </p>

          <h3>
            GHOST did not return a result.
          </h3>

          <p>
            {task.error
              ?? "The selected skill completed without a usable result."}
          </p>
        </section>
      )}


      <section className="panel skills-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">
              CAPABILITIES
            </p>

            <h3>
              Skills
            </h3>
          </div>

          <span className="history-count">
            {skills.length} available
          </span>
        </div>

        {skills.length === 0 ? (
          <div className="history-empty">
            <p>
              GHOST has no skills available.
            </p>
          </div>
        ) : (
          <div className="skills-layout">
            <div className="skills-list">
              {skills.map(
                (skill) => (
                  <button
                    key={skill.name}
                    type="button"
                    className={
                      selectedSkill?.name
                      === skill.name
                        ? "skill-card selected"
                        : "skill-card"
                    }
                    onClick={() =>
                      setSelectedSkill(
                        skill,
                      )
                    }
                  >
                    <div className="skill-card-header">
                      <span className="skill-status-dot" />

                      <strong>
                        {skill.name}
                      </strong>
                    </div>

                    <p>
                      {skill.description}
                    </p>

                    <div className="skill-card-meta">
                      <span>
                        {skill.variables.length}
                        {" "}
                        variables
                      </span>

                      <span>
                        {skill.steps.length}
                        {" "}
                        steps
                      </span>
                    </div>
                  </button>
                ),
              )}
            </div>

            {selectedSkill && (
              <div className="skill-detail">
                <div className="skill-detail-top">
                  <div>
                    <p className="eyebrow">
                      SKILL DEFINITION
                    </p>

                    <h4>
                      {selectedSkill.name}
                    </h4>
                  </div>

                  <span className="skill-ready">
                    Ready
                  </span>
                </div>

                <p className="skill-description">
                  {selectedSkill.description}
                </p>

                <div className="skill-section">
                  <p className="skill-section-title">
                    Inputs
                  </p>

                  <div className="variable-list">
                    {selectedSkill.variables.map(
                      (variable) => (
                        <div
                          key={variable.name}
                          className="variable-card"
                        >
                          <div className="variable-header">
                            <strong>
                              {variable.name}
                            </strong>

                            <code>
                              {variable.example_value}
                            </code>
                          </div>

                          {variable.description && (
                            <p>
                              {variable.description}
                            </p>
                          )}
                        </div>
                      ),
                    )}
                  </div>
                </div>

                <div className="skill-section">
                  <p className="skill-section-title">
                    Steps
                  </p>

                  <div className="learned-steps">
                    {selectedSkill.steps.map(
                      (step, index) => (
                        <div
                          key={`${step.action_type}-${index}`}
                          className="learned-step"
                        >
                          <span className="step-number">
                            {String(
                              index + 1,
                            ).padStart(
                              2,
                              "0",
                            )}
                          </span>

                          <div>
                            <strong>
                              {step.action_type}
                            </strong>

                            <p>
                              {step.target
                                ?? "No target"}

                              {step.value
                                ? ` · ${step.value}`
                                : ""}
                            </p>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </section>


      <section className="panel history-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">
              MEMORY
            </p>

            <h3>
              Recent Runs
            </h3>
          </div>

          <span className="history-count">
            {taskHistory.length} saved
          </span>
        </div>

        {taskHistory.length === 0 ? (
          <div className="history-empty">
            <p>
              GHOST has no saved runs yet.
            </p>
          </div>
        ) : (
          <div className="history-list">
            {taskHistory.map(
              (historyTask) => (
                <button
                  key={historyTask.task_id}
                  type="button"
                  className="history-item"
                  onClick={() =>
                    openHistoryTask(
                      historyTask,
                    )
                  }
                >
                  <div className="history-main">
                    <span
                      className={
                        historyTask.verified
                          ? "history-indicator verified"
                          : "history-indicator failed"
                      }
                    />

                    <div>
                      <strong>
                        {historyTask.query}
                      </strong>

                      <p>
                        {historyTask.skill
                          ?? "Unknown skill"}
                        {" · "}
                        {historyTask.provider}
                      </p>
                    </div>
                  </div>

                  <div className="history-meta">
                    <span
                      className={
                        historyTask.verified
                          ? "history-status verified"
                          : "history-status failed"
                      }
                    >
                      {historyTask.verified
                        ? "Verified"
                        : historyTask.status}
                    </span>

                    <time>
                      {formatTaskDate(
                        historyTask.created_at,
                      )}
                    </time>
                  </div>
                </button>
              ),
            )}
          </div>
        )}
      </section>
    </main>
  );
}


export default App;