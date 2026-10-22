const TOKEN_KEY = "agentic-dev-token";

export function token(): string {
  return sessionStorage.getItem(TOKEN_KEY) || "local-dev-token-not-for-production";
}

export function setToken(value: string): void {
  sessionStorage.setItem(TOKEN_KEY, value);
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      Authorization: `Bearer ${token()}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}
