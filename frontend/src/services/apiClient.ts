const BASE_URL = import.meta.env.VITE_API_URL || '';

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    let message = `Request failed (${response.status})`;
    try {
      const parsed = JSON.parse(errorBody);
      message = parsed.detail || message;
    } catch {
      // use default message
    }
    throw new Error(message);
  }

  return response.json();
}

function postForm<T>(endpoint: string, formData: FormData): Promise<T> {
  return request<T>(endpoint, {
    method: 'POST',
    body: formData,
  });
}

function postFormWithProgress<T>(
  endpoint: string,
  formData: FormData,
  onProgress?: (stage: string) => void,
): Promise<T> {
  onProgress?.('uploading');
  return postForm<T>(endpoint, formData);
}

export { request, postForm, postFormWithProgress, BASE_URL };
