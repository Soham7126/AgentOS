const BRIDGE_URL = process.env.AGENTOS_BRIDGE_URL ?? "http://localhost:8000";

export interface RecallResult {
  text?: string;
  content?: string;
  source?: string;
  [key: string]: unknown;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BRIDGE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Bridge ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

export function remember(content: string, tags?: Record<string, unknown>) {
  return post<{ status: string }>("/remember", { content, tags });
}

export function recall(
  query: string,
  filters?: Record<string, unknown>,
  top_k = 15,
  list_mode = false
) {
  return post<{ results: RecallResult[] }>("/recall", { query, filters, top_k, list_mode });
}

/** Recall every matching fact as separate chunks instead of one synthesized answer. */
export function recallList(query: string, filters?: Record<string, unknown>, top_k = 15) {
  return recall(query, filters, top_k, true);
}

export function improve(session_id?: string) {
  return post<{ status: string; mode?: string; error?: string }>("/improve", { session_id });
}

export function forget(target: string) {
  return post<{ status: string; target: string }>("/forget", { target });
}
