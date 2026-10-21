// In browser, always use relative path ("") so requests match the current origin
// and are proxied via Next.js rewrites to the FastAPI backend on port 8001,
// completely avoiding cross-origin cookie mismatch between localhost and 127.0.0.1.
const API_BASE_URL =
  typeof window !== "undefined"
    ? ""
    : (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001");

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...restOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const defaultHeaders: Record<string, string> = {
    Accept: "application/json",
  };

  // Only add Content-Type: application/json if not FormData
  if (!(restOptions.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  // Attach token from localStorage if present
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("indialeads_token");
    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...restOptions,
    credentials: restOptions.credentials || "include",
    headers: {
      ...defaultHeaders,
      ...(headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    // Intercept 401 Unauthorized for automatic redirection
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("indialeads_token");
      if (!window.location.pathname.startsWith("/login")) {
        const currentPath = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?redirect=${currentPath}`;
      }
    }

    let errorDetail = "An unexpected error occurred.";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      errorDetail = `Request failed with status ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
