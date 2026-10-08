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
  continueGhostAgent,
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


function questionForVariable(
  variable: string,
  skill: string,
) {
  if (
    skill === "verify_project"
    && variable === "project_path"
  ) {
    return "Which project should I verify?";
  }

  return `Provide ${variable}`;
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
    originalRequest,
    setOriginalRequest,
  ] = useState<string | null>(
    null,
  );

  const [
    missingInputs,
    setMissingInputs,
  ] = useState<Record<string, string>>(
    {},
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

      setSkills(learnedSkills);

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


  function selectRoutedSkill(
    skillName: string,
  ) {
    const selected =
      skills.find(
        (skill) =>
          skill.name === skillName,
      );

    if (selected) {
      setSelectedSkill(selected);
    }
  }


  function prepareMissingInputs(
    routed: AgentRoute,
  ) {
    const inputs:
      Record<string, string> = {};

    for (
      const variable
      of routed.missing_variables
    ) {
      inputs[variable] = "";
    }

    setMissingInputs(inputs);
  }


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
    setOriginalRequest(null);
    setMissingInputs({});

    try {
      const response =
        await runGhostAgent({
          request: cleanRequest,
          provider,
        });

      setRoute(response.route);
      setTask(response.task);

      selectRoutedSkill(
        response.route.skill,
      );

      if (response.executed) {
        await loadTaskHistory();
      } else {
        setOriginalRequest(
          cleanRequest,
        );

        prepareMissingInputs(
          response.route,
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


  async function handleContinue(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      !route
      || !originalRequest
    ) {
      return;
    }

    const suppliedVariables = {
      ...route.variables,
    };

    for (
      const variable
      of route.missing_variables
    ) {
      const value =
        missingInputs[
          variable
        ]?.trim();

      if (value) {
        suppliedVariables[
          variable
        ] = value;
      }
    }

    setIsRunning(true);
    setTask(null);
    setError(null);

    try {
      const response =
        await continueGhostAgent({
          original_request:
            originalRequest,
          skill:
            route.skill,
          confidence:
            route.confidence,
          reason:
            route.reason,
          variables:
            suppliedVariables,
          provider,
        });

      setRoute(response.route);
      setTask(response.task);

      selectRoutedSkill(
        response.route.skill,
      );

      if (response.executed) {
        setOriginalRequest(null);
        setMissingInputs({});

        await loadTaskHistory();
      } else {
        prepareMissingInputs(
          response.route,
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
    setTask(historyTask);

    setRoute(null);
    setError(null);
    setOriginalRequest(null);
    setMissingInputs({});

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

  const verifiedRuns =
    taskHistory.filter(
      (historyTask) =>
        historyTask.verified,
    ).length;


  return (
    <main className="ghost-os">
      <header className="system-header">
        <div className="brand-cluster">
          <div className="ghost-emblem">
            <img
              src="/ghost-logo.png"
              alt=""
            />
          </div>

          <div>
            <div className="header-title">
              GHOST
            </div>

            <div className="header-subtitle">
              OBSERVE. LEARN. AUTOMATE.
            </div>
          </div>
        </div>

        <div
          className={
            backendOnline
              ? "system-pill online"
              : "system-pill offline"
          }
        >
          <span />

          {backendOnline
            ? "GHOST ONLINE"
            : "GHOST OFFLINE"}
        </div>
      </header>


      <section className="presence-stage">
        <aside className="awareness-panel">
          <div className="micro-heading">
            AWARENESS
          </div>

          <div className="awareness-list">
            <div className="awareness-row">
              <span>
                BACKEND
              </span>

              <strong
                className={
                  backendOnline
                    ? "good"
                    : "bad"
                }
              >
                {backendOnline
                  ? "CONNECTED"
                  : "OFFLINE"}
              </strong>
            </div>

            <div className="awareness-row">
              <span>
                MEMORY
              </span>

              <strong>
                {taskHistory.length}
                {" "}
                RUNS
              </strong>
            </div>

            <div className="awareness-row">
              <span>
                VERIFIED
              </span>

              <strong className="good">
                {verifiedRuns}
              </strong>
            </div>

            <div className="awareness-row">
              <span>
                SKILLS
              </span>

              <strong>
                {skills.length}
              </strong>
            </div>

            <div className="awareness-row">
              <span>
                ROUTER
              </span>

              <strong className="good">
                {backendOnline
                  ? "LISTENING"
                  : "DORMANT"}
              </strong>
            </div>
          </div>

          <div className="awareness-footer">
            GHOST observes execution,
            remembers outcomes, and selects
            capabilities from learned behavior.
          </div>
        </aside>


        <section className="entity-stage">
          <span className="entity-label">
            GHOST // PRESENCE
          </span>

          <span className="entity-state">
            {isRunning
              ? "PROCESSING"
              : "AWAITING DIRECTIVE"}
          </span>

          <div
            className={
              isRunning
                ? "presence-core active"
                : "presence-core"
            }
          >
            <div className="presence-aura" />

            <div className="arc arc-one" />
            <div className="arc arc-two" />
            <div className="arc arc-three" />
            <div className="arc arc-four" />

            <span className="particle particle-one" />
            <span className="particle particle-two" />
            <span className="particle particle-three" />
            <span className="particle particle-four" />
            <span className="particle particle-five" />

            <div className="ghost-wordmark">
              <span className="ghost-name">
                GHOST
              </span>

              <span className="ghost-chevron">
                ▾
              </span>
            </div>
          </div>

          <div className="entity-status">
            STATE //
            {" "}
            <strong>
              {isRunning
                ? "THINKING"
                : "LISTENING"}
            </strong>
          </div>

          <div className="entity-readout">
            <div>
              <span>
                ACTIVE SKILL
              </span>

              <strong>
                {route?.skill
                  ?? selectedSkill?.name
                  ?? "NONE"}
              </strong>
            </div>

            <div>
              <span>
                CONFIDENCE
              </span>

              <strong>
                {route
                  ? `${Math.round(
                    route.confidence
                    * 100,
                  )}%`
                  : "--"}
              </strong>
            </div>

            <div>
              <span>
                EXECUTION
              </span>

              <strong>
                {isRunning
                  ? "ACTIVE"
                  : task
                    ? task.status
                      .toUpperCase()
                    : "IDLE"}
              </strong>
            </div>
          </div>
        </section>


        <aside className="capability-panel">
          <div className="micro-heading">
            CAPABILITIES
          </div>

          <div className="capability-list">
            {skills.map(
              (skill) => (
                <button
                  key={skill.name}
                  type="button"
                  className={
                    selectedSkill?.name
                    === skill.name
                      ? "capability-node active"
                      : "capability-node"
                  }
                  onClick={() =>
                    setSelectedSkill(
                      skill,
                    )
                  }
                >
                  <span>
                    <strong>
                      {skill.name}
                    </strong>

                    <small>
                      {skill.steps.length}
                      {" "}
                      steps //
                      {" "}
                      {skill.variables.length}
                      {" "}
                      inputs
                    </small>
                  </span>

                  <span className="capability-dot" />
                </button>
              ),
            )}
          </div>
        </aside>
      </section>


      <section className="command-deck">
        <div className="command-label">
          DIRECTIVE
        </div>

        <form onSubmit={handleSubmit}>
          <div className="command-entry">
            <span className="command-prefix">
              &gt;
            </span>

            <textarea
              value={request}
              onChange={(event) =>
                setRequest(
                  event.target.value,
                )
              }
              rows={2}
              spellCheck={false}
              placeholder="Tell GHOST what you want..."
            />

            <button
              type="submit"
              className="execute-button"
              disabled={
                isRunning
                || !backendOnline
              }
            >
              {isRunning
                ? "PROCESSING"
                : "EXECUTE"}
            </button>
          </div>

          <div className="command-options">
            <div className="provider-control">
              <label>
                WEB PROVIDER
              </label>

              <select
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

            <span className="command-path">
              UNDERSTAND → CHOOSE →
              ACT → VERIFY → REMEMBER
            </span>
          </div>
        </form>
      </section>


      {isRunning && (
        <section className="execution-trace">
          <span className="trace-label">
            EXECUTION
          </span>

          <span className="trace-step active">
            UNDERSTANDING
          </span>

          <div className="trace-line" />

          <span className="trace-step active">
            RESOLVING
          </span>

          <div className="trace-line" />

          <span className="trace-step">
            VERIFYING
          </span>
        </section>
      )}


      {route && (
        <section className="route-strip">
          <div>
            <span>
              ROUTE
            </span>

            <strong>
              {route.skill}
            </strong>
          </div>

          <div>
            <span>
              CONFIDENCE
            </span>

            <strong>
              {Math.round(
                route.confidence
                * 100,
              )}
              %
            </strong>
          </div>

          <div>
            <span>
              INPUTS
            </span>

            <strong>
              {
                Object.keys(
                  route.variables,
                ).length
              }
            </strong>
          </div>

          <p>
            {route.reason}
          </p>
        </section>
      )}


      {error && (
        <section className="alert-panel">
          <span className="alert-code">
            !
          </span>

          <div>
            <strong>
              GHOST EXECUTION FAILURE
            </strong>

            <p>
              {error}
            </p>
          </div>
        </section>
      )}


      {route
        && originalRequest
        && route.missing_variables.length
        > 0 && (
        <section className="input-request-panel">
          <div className="input-request-header">
            <div>
              <span>
                ADDITIONAL INPUT REQUIRED
              </span>

              <h2>
                {questionForVariable(
                  route
                    .missing_variables[0],
                  route.skill,
                )}
              </h2>
            </div>

            <span>
              {route.skill}
            </span>
          </div>

          <form
            className="continue-form"
            onSubmit={handleContinue}
          >
            {route.missing_variables.map(
              (variable) => (
                <label
                  key={variable}
                  className="missing-field"
                >
                  <span>
                    {variable}
                  </span>

                  <input
                    value={
                      missingInputs[
                        variable
                      ]
                      ?? ""
                    }
                    onChange={(event) =>
                      setMissingInputs(
                        (
                          current,
                        ) => ({
                          ...current,
                          [variable]:
                            event.target
                              .value,
                        }),
                      )
                    }
                    placeholder={
                      variable
                      === "project_path"
                        ? "~/Desktop/ghost"
                        : variable
                    }
                  />
                </label>
              ),
            )}

            <button
              type="submit"
              className="continue-button"
              disabled={
                isRunning
                || !backendOnline
              }
            >
              CONTINUE
            </button>
          </form>
        </section>
      )}


      {task && researchResult && (
        <section className="data-panel">
          <div className="data-header">
            <div>
              <span className="micro-label">
                RESEARCH RESULT
              </span>

              <h2>
                {researchResult.title
                  ?? task.query}
              </h2>
            </div>

            <span
              className={
                task.success
                  ? "verification-tag good"
                  : "verification-tag bad"
              }
            >
              {task.success
                ? "VERIFIED"
                : "FAILED"}
            </span>
          </div>

          <div className="data-meta">
            <span>
              {task.skill}
            </span>

            <span>
              {task.provider}
            </span>

            <span>
              TASK {task.task_id}
            </span>
          </div>

          <p className="result-summary">
            {researchResult.summary}
          </p>

          <div className="term-grid">
            {researchResult.key_terms.map(
              (term) => (
                <span key={term}>
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
              OPEN SOURCE //
              {" "}
              {researchResult.domain}
            </a>
          )}
        </section>
      )}


      {task && projectResult && (
        <section className="data-panel">
          <div className="data-header">
            <div>
              <span className="micro-label">
                PROJECT VERIFICATION
              </span>

              <h2>
                {
                  projectResult
                    .project
                    .project_path
                }
              </h2>
            </div>

            <span
              className={
                task.verified
                  ? "verification-tag good"
                  : "verification-tag bad"
              }
            >
              {task.verified
                ? "VERIFIED"
                : "FAILED"}
            </span>
          </div>

          <div className="verification-grid">
            <div>
              <strong>
                {
                  projectResult
                    .summary
                    .total_checks
                }
              </strong>

              <span>
                CHECKS
              </span>
            </div>

            <div>
              <strong>
                {
                  projectResult
                    .summary
                    .passed
                }
              </strong>

              <span>
                PASSED
              </span>
            </div>

            <div>
              <strong>
                {
                  projectResult
                    .summary
                    .failed
                }
              </strong>

              <span>
                FAILED
              </span>
            </div>
          </div>

          <div className="stack-row">
            {projectResult
              .project
              .project_types
              .map(
                (type) => (
                  <span key={type}>
                    {type}
                  </span>
                ),
              )}
          </div>

          <div className="check-list">
            {projectResult
              .checks
              .map(
                (check) => (
                  <div
                    key={
                      `${check.component}-${check.name}`
                    }
                    className="check-row"
                  >
                    <span
                      className={
                        check.success
                          ? "check-node passed"
                          : "check-node failed"
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
                        {" // "}
                        {
                          check.command
                            .join(" ")
                        }
                      </p>
                    </div>

                    <span
                      className={
                        check.success
                          ? "check-result passed"
                          : "check-result failed"
                      }
                    >
                      {check.success
                        ? "PASS"
                        : "FAIL"}
                    </span>
                  </div>
                ),
              )}
          </div>
        </section>
      )}


      {task && !task.result && (
        <section className="alert-panel">
          <span className="alert-code">
            !
          </span>

          <div>
            <strong>
              NO RESULT RETURNED
            </strong>

            <p>
              {task.error
                ?? "The selected skill completed without a usable result."}
            </p>
          </div>
        </section>
      )}


      <section className="lower-grid">
        <section className="data-panel">
          <div className="data-header">
            <div>
              <span className="micro-label">
                SKILL INSPECTOR
              </span>

              <h2>
                {selectedSkill?.name
                  ?? "No skill selected"}
              </h2>
            </div>

            <span className="verification-tag good">
              READY
            </span>
          </div>

          {selectedSkill && (
            <>
              <p className="inspector-description">
                {selectedSkill.description}
              </p>

              <div className="inspector-section">
                <span className="micro-label">
                  VARIABLES
                </span>

                <div className="variable-grid">
                  {selectedSkill
                    .variables
                    .map(
                      (variable) => (
                        <div
                          key={variable.name}
                          className="variable-node"
                        >
                          <strong>
                            {variable.name}
                          </strong>

                          <code>
                            {
                              variable
                                .example_value
                            }
                          </code>

                          <p>
                            {
                              variable
                                .description
                            }
                          </p>
                        </div>
                      ),
                    )}
                </div>
              </div>

              <div className="inspector-section">
                <span className="micro-label">
                  EXECUTION SEQUENCE
                </span>

                <div className="step-list">
                  {selectedSkill
                    .steps
                    .map(
                      (
                        step,
                        index,
                      ) => (
                        <div
                          key={
                            `${step.action_type}-${index}`
                          }
                          className="step-node"
                        >
                          <span>
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
                                ?? "system"}

                              {step.value
                                ? ` // ${step.value}`
                                : ""}
                            </p>
                          </div>
                        </div>
                      ),
                    )}
                </div>
              </div>
            </>
          )}
        </section>


        <section className="data-panel">
          <div className="data-header">
            <div>
              <span className="micro-label">
                MEMORY
              </span>

              <h2>
                Recent Executions
              </h2>
            </div>

            <span className="memory-count">
              {taskHistory.length}
            </span>
          </div>

          <div className="memory-list">
            {taskHistory.length === 0 && (
              <div className="empty-memory">
                NO EXECUTIONS RECORDED
              </div>
            )}

            {taskHistory.map(
              (historyTask) => (
                <button
                  key={
                    historyTask.task_id
                  }
                  type="button"
                  className="memory-row"
                  onClick={() =>
                    openHistoryTask(
                      historyTask,
                    )
                  }
                >
                  <span
                    className={
                      historyTask.verified
                        ? "memory-light good"
                        : "memory-light bad"
                    }
                  />

                  <span className="memory-content">
                    <strong>
                      {historyTask.query}
                    </strong>

                    <small>
                      {historyTask.skill
                        ?? "unknown"}
                      {" // "}
                      {historyTask.provider}
                    </small>
                  </span>

                  <span className="memory-right">
                    <b>
                      {historyTask.verified
                        ? "VERIFIED"
                        : historyTask.status
                          .toUpperCase()}
                    </b>

                    <small>
                      {formatTaskDate(
                        historyTask
                          .created_at,
                      )}
                    </small>
                  </span>
                </button>
              ),
            )}
          </div>
        </section>
      </section>


      <footer className="system-footer">
        <span>
          GHOST
        </span>

        <span>
          OBSERVE // LEARN // AUTOMATE
        </span>
      </footer>
    </main>
  );
}


export default App;