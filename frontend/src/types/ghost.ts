export type ResearchResult = {
  title: string | null;
  url: string | null;
  domain: string | null;
  summary: string | null;
  key_terms: string[];
  summary_source: string | null;
};

export type GhostTask = {
  task_id: number;
  status: string;
  query: string;
  provider: string;
  success: boolean | null;
  verified: boolean | null;
  skill: string | null;
  result: ResearchResult | null;
  error: string | null;
  created_at: string | null;
  completed_at: string | null;
};

export type CreateGhostTaskRequest = {
  query: string;
  provider: string;
};

export type SkillVariable = {
  name: string;
  example_value: string;
  description: string | null;
};

export type SkillStep = {
  action_type: string;
  target: string | null;
  value: string | null;
  url: string | null;
};

export type GhostSkill = {
  name: string;
  description: string;
  variables: SkillVariable[];
  steps: SkillStep[];
};