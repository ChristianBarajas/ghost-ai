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
} from "./services/ghostApi";

import type {
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


  useEffect(() => {
    async function checkHealth() {
      try {
        await checkGhostHealth();

        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    }

    checkHealth();
  }, []);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanQuery = query.trim();

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
          <label
            htmlFor="ghost-query"
          >
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
              <label
                htmlFor="provider"
              >
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
                Executing learned research workflow...
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
                Generating AI result...
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
                  ?? "GHOST Result"}
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
              Skill:
              {" "}
              {task.skill}
            </span>

            <span>
              Provider:
              {" "}
              {task.provider}
            </span>

            <span>
              Task:
              {" "}
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
    </main>
  );
}


export default App;