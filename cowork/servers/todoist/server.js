"use strict";

const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const { z } = require("zod");

// --- Token validation ---
const TOKEN = process.env.TODOIST_API_TOKEN;
if (!TOKEN) {
  process.stderr.write(
    "[todoist-mcp] TODOIST_API_TOKEN is not set. " +
    "Get your token from https://todoist.com/app/settings/integrations/developer " +
    "and set it in your environment.\n"
  );
  process.exit(1);
}

// --- Response trimming ---
const STRIP_FIELDS = new Set([
  "user_id", "added_by_uid", "assigned_by_uid", "responsible_uid",
  "duration", "is_collapsed", "completed_by_uid", "day_order", "goal_ids",
]);

function stripTask(task) {
  const out = {};
  for (const [k, v] of Object.entries(task)) {
    if (!STRIP_FIELDS.has(k)) out[k] = v;
  }
  return out;
}

function stripTasks(data) {
  if (Array.isArray(data)) return data.map(stripTask);
  if (data && typeof data === "object") {
    // Strip any top-level array values (results, items, tasks, etc.)
    const out = {};
    for (const [k, v] of Object.entries(data)) {
      out[k] = Array.isArray(v) ? v.map(stripTask) : v;
    }
    return out;
  }
  return data;
}

// --- API helpers ---
const API_BASE = "https://api.todoist.com/api/v1";

async function apiGet(path, params) {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) {
    throw new Error(`Todoist API ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) {
    throw new Error(`Todoist API ${res.status}: ${await res.text()}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) {
    throw new Error(`Todoist API ${res.status}: ${await res.text()}`);
  }
  return null;
}

function toText(data) {
  return { content: [{ type: "text", text: JSON.stringify(stripTasks(data), null, 2) }] };
}

// --- MCP Server ---
const server = new McpServer({
  name: "todoist",
  version: "1.0.0",
});

// get_tasks
server.tool(
  "get_tasks",
  "Get open tasks from Todoist. Use Todoist filter language for the filter parameter. " +
  "Examples: 'today' (due today), 'overdue' (past due), 'p1' (priority 1/urgent), " +
  "'#Inbox' (inbox project), 'due before: +7 days' (due this week). " +
  "Filters can be combined with & (and) or | (or).",
  {
    filter: z.string().optional().describe(
      "Todoist filter string. Examples: 'today', 'overdue', '#ProjectName', 'p1 & due before: +7 days'"
    ),
    project_id: z.string().optional().describe("Filter by project ID"),
  },
  async ({ filter, project_id }) => {
    const params = {};
    if (filter) params.filter = filter;
    if (project_id) params.project_id = project_id;
    const tasks = await apiGet("/tasks", params);
    return toText(tasks);
  }
);

// get_completed_tasks
server.tool(
  "get_completed_tasks",
  "Get completed tasks from Todoist within an optional date range. " +
  "Uses the Sync API which returns completed item history.",
  {
    since: z.string().optional().describe("Start date in YYYY-MM-DD format (inclusive)"),
    until: z.string().optional().describe("End date in YYYY-MM-DD format (inclusive)"),
    project_id: z.string().optional().describe("Filter by project ID"),
    limit: z.number().int().min(1).max(200).optional().describe("Max tasks to return (default 50, max 200)"),
  },
  async ({ since, until, project_id, limit }) => {
    const params = { limit: limit ?? 50 };
    if (since) params.since = `${since}T00:00:00Z`;
    if (until) params.until = `${until}T23:59:59Z`;
    if (project_id) params.project_id = project_id;
    const data = await apiGet("/tasks/completed_by_completion_date", params);
    return toText(data);
  }
);

// create_task
server.tool(
  "create_task",
  "Create a new task in Todoist.",
  {
    content: z.string().describe("Task title"),
    project_id: z.string().optional().describe("Project ID. Omit to add to Inbox."),
    due_string: z.string().optional().describe("Natural language due date, e.g. 'today', 'tomorrow', 'next Monday'"),
    due_date: z.string().optional().describe("Due date in YYYY-MM-DD format"),
    priority: z.number().int().min(1).max(4).optional().describe(
      "Priority level: 1=normal (p4 in UI), 2=medium (p3), 3=high (p2), 4=urgent (p1)"
    ),
    description: z.string().optional().describe("Task description/notes"),
    labels: z.array(z.string()).optional().describe("Label names to apply"),
  },
  async ({ content, project_id, due_string, due_date, priority, description, labels }) => {
    const body = { content };
    if (project_id) body.project_id = project_id;
    if (due_string) body.due_string = due_string;
    if (due_date) body.due_date = due_date;
    if (priority !== undefined) body.priority = priority;
    if (description) body.description = description;
    if (labels) body.labels = labels;
    const task = await apiPost("/tasks", body);
    return toText(task);
  }
);

// update_task
server.tool(
  "update_task",
  "Update an existing Todoist task. Only provided fields are changed.",
  {
    task_id: z.string().describe("The task ID to update"),
    content: z.string().optional().describe("New task title"),
    due_string: z.string().optional().describe("Natural language due date, e.g. 'tomorrow', 'next Monday'"),
    due_date: z.string().optional().describe("Due date in YYYY-MM-DD format"),
    priority: z.number().int().min(1).max(4).optional().describe(
      "Priority: 1=normal (p4 in UI), 2=medium (p3), 3=high (p2), 4=urgent (p1)"
    ),
    project_id: z.string().optional().describe("Move task to this project ID"),
    description: z.string().optional().describe("Task description/notes"),
    labels: z.array(z.string()).optional().describe("Replace all labels with this array"),
  },
  async ({ task_id, ...updates }) => {
    const body = {};
    for (const [k, v] of Object.entries(updates)) {
      if (v !== undefined) body[k] = v;
    }
    const task = await apiPost(`/tasks/${task_id}`, body);
    return toText(task);
  }
);

// complete_task
server.tool(
  "complete_task",
  "Mark a Todoist task as complete.",
  {
    task_id: z.string().describe("The task ID to mark as complete"),
  },
  async ({ task_id }) => {
    await apiPost(`/tasks/${task_id}/close`);
    return { content: [{ type: "text", text: `Task ${task_id} marked as complete.` }] };
  }
);

// delete_task
server.tool(
  "delete_task",
  "Permanently delete a Todoist task.",
  {
    task_id: z.string().describe("The task ID to delete"),
  },
  async ({ task_id }) => {
    await apiDelete(`/tasks/${task_id}`);
    return { content: [{ type: "text", text: `Task ${task_id} deleted.` }] };
  }
);

// get_projects
server.tool(
  "get_projects",
  "Get all projects from Todoist.",
  {},
  async () => {
    const projects = await apiGet("/projects");
    return toText(projects);
  }
);

// add_task_comment
server.tool(
  "add_task_comment",
  "Add a comment to a Todoist task.",
  {
    task_id: z.string().describe("The task ID to comment on"),
    content: z.string().describe("Comment text (supports markdown)"),
  },
  async ({ task_id, content }) => {
    const comment = await apiPost("/comments", { task_id, content });
    return toText(comment);
  }
);

// --- Connect ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  process.stderr.write(`[todoist-mcp] Fatal error: ${err.message}\n`);
  process.exit(1);
});
