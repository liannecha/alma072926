const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export type Lead = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  resume_original_filename: string;
  resume_content_type: string;
  status: 'PENDING' | 'REACHED_OUT';
  created_at: string;
  updated_at: string;
  reached_out_at: string | null;
};

async function getErrorMessage(response: Response, fallback: string) {
  const data = await response.json().catch(() => null);
  if (typeof data?.detail === 'string') {
    return data.detail;
  }
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    return data.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(' ');
  }
  return fallback;
}

export async function createLead(formData: FormData) {
  const response = await fetch(`${API_BASE_URL}/api/leads`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'Unable to submit lead'));
  }

  return response.json() as Promise<Lead>;
}

export async function listLeads(token: string) {
  const response = await fetch(`${API_BASE_URL}/api/leads`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'Could not load leads'));
  }

  return response.json() as Promise<Lead[]>;
}

export async function markLeadReachedOut(id: number, token: string) {
  const response = await fetch(`${API_BASE_URL}/api/leads/${id}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ status: 'REACHED_OUT' }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'Unable to update lead'));
  }

  return response.json() as Promise<Lead>;
}

export async function downloadLeadResume(id: number, token: string, filename: string) {
  const response = await fetch(`${API_BASE_URL}/api/leads/${id}/resume`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'Unable to download resume'));
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = downloadUrl;
  anchor.download = filename || `lead-${id}-resume`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
