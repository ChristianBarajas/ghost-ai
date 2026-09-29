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
} from "./services/ghostApi";

import type {
  GhostSkill,
  GhostTask,
} from "./types/ghost";


function App() {
  const [
    query,
    setQuery,
  ] = useState(
    "What is retrieval augmented generation?",
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
      // History failure should not block
      // the rest of the interface.
    }
  }


  async function loadSkills() {
    try {
      const learnedSkills =
        await getGhostSkills();

      setSkills(learnedSkills);

      if (
        learnedSkills.length > 0
        && !selectedSkill
      ) {
        const preferredSkill =
          learnedSkills.find(
            (skill) =>
              skill.name === "research_topic",
          )
          ?? learnedSkills[0];

        setSelectedSkill(preferredSkill);
      }
    } catch {
      // Skill loading failure should not
      // block task execution.
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

    const cleanQuery =
      query.trim();

    if (!cleanQuery) {
      return;
    }

    setIsRunning(true);
    setTask(null);
    setError(null);

    try {
      const result =
        await createGhostTask({
          query: cleanQuery,
          provider,
        });

      setTask(result);

      await loadTaskHistory();
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
            GHOST uses learned workflows,
            browser automation, source validation,
            and AI reasoning to complete tasks.
          </p>
        </div>

        <form
          className="task-form"
          onSubmit={handleSubmit}
        >
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
                EXECUTION
              </p>

              <h3>
                GHOST is running
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
                Executing learned workflow...
              </p>
            </div>

            <div className="execution-step">
              <span>
                02
              </span>

              <p>
                Evaluating sources...
              </p>
            </div>

            <div className="execution-step">
              <span>
                03
              </span>

              <p>
                Generating verified result...
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


      {task && (
        <section className="panel result-panel">
          <div className="result-header">
            <div>
              <p className="eyebrow">
                RESULT
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

          {task.error && (
            <div className="summary-card">
              <p className="summary">
                {task.error}
              </p>
            </div>
          )}
        </section>
      )}


      <section className="panel skills-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">
              LEARNED CAPABILITIES
            </p>

            <h3>
              Skills
            </h3>
          </div>

          <span className="history-count">
            {skills.length} learned
          </span>
        </div>

        {skills.length === 0 ? (
          <div className="history-empty">
            <p>
              GHOST has not learned any skills yet.
            </p>

            <span>
              Learned workflows will appear here.
            </span>
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
                        variable
                        {skill.variables.length === 1
                          ? ""
                          : "s"}
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
                      SKILL MEMORY
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
                    Learned Steps
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

            <span>
              Completed tasks will appear here.
            </span>
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