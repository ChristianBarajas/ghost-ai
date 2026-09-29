import type {
  CreateGhostTaskRequest,
  GhostSkill,
  GhostTask,
} from "../types/ghost";

const API_BASE_URL =
  "http://127.0.0.1:8000";


export async function checkGhostHealth() {
  const response = await fetch(
    `${API_BASE_URL}/api/health`,
  );

  if (!response.ok) {
    throw new Error(
      "GHOST backend is unavailable.",
    );
  }

  return response.json();
}


export async function createGhostTask(
  payload: CreateGhostTaskRequest,
): Promise<GhostTask> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(
      `GHOST request failed with status ${response.status}`,
    );
  }

  return response.json();
}


export async function getGhostTasks(): Promise<
  GhostTask[]
> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks`,
  );

  if (!response.ok) {
    throw new Error(
      `Could not load task history: ${response.status}`,
    );
  }

  return response.json();
}


export async function getGhostSkills(): Promise<
  GhostSkill[]
> {
  const response = await fetch(
    `${API_BASE_URL}/api/skills`,
  );

  if (!response.ok) {
    throw new Error(
      `Could not load GHOST skills: ${response.status}`,
    );
  }

  return response.json();
}


export async function getGhostSkill(
  skillName: string,
): Promise<GhostSkill> {
  const response = await fetch(
    `${API_BASE_URL}/api/skills/${encodeURIComponent(
      skillName,
    )}`,
  );

  if (!response.ok) {
    throw new Error(
      `Could not load skill: ${response.status}`,
    );
  }

  return response.json();
}