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
  createGhostTask,
  getGhostSkills,
  getGhostTasks,
  verifyGhostProject,
} from "./services/ghostApi";

import type {
  GhostSkill,
  GhostTask,
  ProjectVerificationResponse,
} from "./types/ghost";


type TaskMode =
  | "research"
  | "verify_project";


function App() {
  const [
    mode,
    setMode,
  ] = useState<TaskMode>(
    "research",
  );

  const [
    query,
    setQuery,
  ] = useState(
    "What is retrieval augmented generation?",
  );

  const [
    projectPath,
    setProjectPath,
  ] = useState(
    "~/Desktop/ghost",
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
    projectResult,
    setProjectResult,
  ] = useState<ProjectVerificationResponse | null>(
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
      const tasks = await getGhostTasks();

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


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setIsRunning(true);
    setTask(null);
    setProjectResult(null);
    setError(null);

    try {
      if (mode === "research") {
        const cleanQuery =
          query.trim();

        if (!cleanQuery) {
          return;
        }

        const result =
          await createGhostTask({
            query: cleanQuery,
            provider,
          });

        setTask(result);

        await loadTaskHistory();
      }

      if (mode === "verify_project") {
        const cleanPath =
          projectPath.trim();

        if (!cleanPath) {
          return;
        }

        const result =
          await verifyGhostProject(
            cleanPath,
          );

        setProjectResult(result);

        await loadTaskHistory();
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
    setMode("research");
    setProjectResult(null);
    setTask(historyTask);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }


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
            Give GHOST a task.
          </h2>

          <p>
            GHOST uses reusable skills,
            specialized execution engines,
            automation, and verification to
            complete tasks.
          </p>
        </div>

        <div className="mode-switcher">
          <button
            type="button"
            className={
              mode === "research"
                ? "mode-button active"
                : "mode-button"
            }
            onClick={() =>
              setMode("research")
            }
          >
            Research
          </button>

          <button
            type="button"
            className={
              mode === "verify_project"
                ? "mode-button active"
                : "mode-button"
            }
            onClick={() =>
              setMode(
                "verify_project",
              )
            }
          >
            Verify Project
          </button>
        </div>

        <form
          className="task-form"
          onSubmit={handleSubmit}
        >
          {mode === "research" ? (
            <>
              <label htmlFor="ghost-query">
                What should GHOST research?
              </label>

              <textarea
                id="ghost-query"
                value={query}
                onChange={(event) =>
                  setQuery(
                    event.target.value,
                  )
                }
                placeholder="Ask GHOST to research something..."
                rows={4}
              />

              <div className="form-footer">
                <div className="provider-control">
                  <label htmlFor="provider">
                    Provider
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
                    ? "GHOST is working..."
                    : "Run Research"}
                </button>
              </div>
            </>
          ) : (
            <>
              <label htmlFor="project-path">
                Which project should GHOST verify?
              </label>

              <textarea
                id="project-path"
                value={projectPath}
                onChange={(event) =>
                  setProjectPath(
                    event.target.value,
                  )
                }
                placeholder="~/Desktop/my-project"
                rows={2}
              />

              <div className="project-hint">
                GHOST will inspect the stack and
                run only supported verification
                checks.
              </div>

              <div className="form-footer project-footer">
                <div className="provider-control">
                  <label>
                    Skill
                  </label>

                  <span className="selected-skill-label">
                    verify_project
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={
                    isRunning
                    || !backendOnline
                  }
                >
                  {isRunning
                    ? "Verifying project..."
                    : "Verify Project"}
                </button>
              </div>
            </>
          )}
        </form>
      </section>


      {isRunning && (
        <section className="panel execution-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                EXECUTION
              </p>

              <h3>
                GHOST is running
              </h3>
            </div>

            <div className="spinner" />
          </div>

          <div className="execution-list">
            {mode === "research" ? (
              <>
                <div className="execution-step active">
                  <span>01</span>

                  <p>
                    Executing research workflow...
                  </p>
                </div>

                <div className="execution-step">
                  <span>02</span>

                  <p>
                    Evaluating sources...
                  </p>
                </div>

                <div className="execution-step">
                  <span>03</span>

                  <p>
                    Verifying result...
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="execution-step active">
                  <span>01</span>

                  <p>
                    Inspecting project stack...
                  </p>
                </div>

                <div className="execution-step">
                  <span>02</span>

                  <p>
                    Building verification plan...
                  </p>
                </div>

                <div className="execution-step">
                  <span>03</span>

                  <p>
                    Running safe checks...
                  </p>
                </div>
              </>
            )}
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


      {task && (
        <section className="panel result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                RESEARCH RESULT
              </p>

              <h3>
                {task.result?.title
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

          {task.result && (
            <>
              <div className="summary-card">
                <p className="summary">
                  {task.result.summary}
                </p>
              </div>

              <div className="terms">
                {task.result.key_terms.map(
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

              {task.result.url && (
                <a
                  className="source-link"
                  href={task.result.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  View source
                  {" → "}
                  {task.result.domain}
                </a>
              )}
            </>
          )}
        </section>
      )}


      {projectResult && projectResult.result && (
        <section className="panel project-result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                PROJECT VERIFICATION
              </p>

              <h3>
                {
                  projectResult.result
                    .project.project_path
                }
              </h3>
            </div>

            <div
              className={
                projectResult.verified
                  ? "result-badge success"
                  : "result-badge failure"
              }
            >
              {projectResult.verified
                ? "Verified"
                : "Failed"}
            </div>
          </div>

          <div className="verification-stats">
            <div>
              <strong>
                {
                  projectResult.result
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
                  projectResult.result
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
                  projectResult.result
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
                projectResult.result
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
              projectResult.result
                .checks.map(
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
                          {check.command.join(" ")}
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


      {projectResult && !projectResult.result && (
        <section className="panel error-panel">
          <p className="eyebrow">
            PROJECT VERIFICATION
          </p>

          <h3>
            No verification result was returned.
          </h3>

          <p>
            {projectResult.error
              ?? "The verification run did not produce a result."}
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