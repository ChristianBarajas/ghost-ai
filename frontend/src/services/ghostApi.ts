import type {
    CreateGhostTaskRequest,
    GhostTask,
  } from "../types/ghost";
  
  const API_BASE_URL = "http://127.0.0.1:8000";
  
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