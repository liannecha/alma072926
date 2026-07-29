'use client';

import { signIn, signOut, useSession } from 'next-auth/react';
import { useEffect, useMemo, useState } from 'react';
import { Lead, deleteLead, downloadLeadResume, listLeads, markLeadPending, markLeadReachedOut, sendLeadEmail } from '../../lib/api';

const STORAGE_KEY = 'alma-internal-token';

export default function AdminPage() {
  const { data: session, status } = useSession();
  const [fallbackToken, setFallbackToken] = useState('');
  const [savedFallbackToken, setSavedFallbackToken] = useState('');
  const [googleAuthEnabled, setGoogleAuthEnabled] = useState<boolean | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [sendingEmailId, setSendingEmailId] = useState<number | null>(null);
  const [emailFeedback, setEmailFeedback] = useState<{ leadId: number; message: string; kind: 'success' | 'error' } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const googleToken = session?.googleIdToken || '';
  const activeToken = googleToken || savedFallbackToken;
  const isAuthenticated = Boolean(activeToken);
  const signedInEmail = session?.user?.email || '';

  const loadLeads = async (activeToken: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listLeads(activeToken);
      setLeads(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load leads');
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEY) || '';
    setSavedFallbackToken(storedToken);
    setFallbackToken(storedToken);
  }, []);

  useEffect(() => {
    const loadAuthConfig = async () => {
      const response = await fetch('/api/auth/google-enabled');
      const payload = (await response.json()) as { enabled?: boolean };
      setGoogleAuthEnabled(Boolean(payload.enabled));
    };

    void loadAuthConfig().catch(() => setGoogleAuthEnabled(false));
  }, []);

  useEffect(() => {
    if (activeToken) {
      void loadLeads(activeToken);
    } else {
      setLeads([]);
    }
  }, [activeToken]);

  const handleFallbackContinue = async () => {
    const trimmedToken = fallbackToken.trim();
    if (!trimmedToken) {
      setError('Enter your internal token');
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, trimmedToken);
    setSavedFallbackToken(trimmedToken);
  };

  const handleSignOut = async () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setSavedFallbackToken('');
    setFallbackToken('');
    setLeads([]);
    setError(null);
    if (status === 'authenticated') {
      await signOut({ callbackUrl: '/admin' });
    }
  };

  const handleStatusChange = async (lead: Lead) => {
    if (!activeToken) {
      return;
    }

    if (lead.status === 'REACHED_OUT') {
      const confirmed = window.confirm(`Are you sure you want to move ${lead.first_name} ${lead.last_name} back to pending?`);
      if (!confirmed) {
        return;
      }
    }

    try {
      const updatedLead = lead.status === 'PENDING'
        ? await markLeadReachedOut(lead.id, activeToken)
        : await markLeadPending(lead.id, activeToken);
      setLeads((current) => current.map((item) => (item.id === lead.id ? updatedLead : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update lead');
    }
  };

  const handleDownloadResume = async (lead: Lead) => {
    if (!activeToken) {
      return;
    }

    try {
      await downloadLeadResume(lead.id, activeToken, lead.resume_original_filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to download resume');
    }
  };

  const handleSendEmail = async (lead: Lead) => {
    if (!activeToken || sendingEmailId !== null) {
      return;
    }

    setSendingEmailId(lead.id);
    setEmailFeedback(null);
    try {
      const result = await sendLeadEmail(lead.id, activeToken);
      setEmailFeedback({ leadId: lead.id, message: result.detail, kind: 'success' });
    } catch (err) {
      setEmailFeedback({
        leadId: lead.id,
        message: err instanceof Error ? err.message : 'Unable to send email',
        kind: 'error',
      });
    } finally {
      setSendingEmailId(null);
    }
  };

  const handleDeleteLead = async (lead: Lead) => {
    if (!activeToken) {
      return;
    }

    const confirmed = window.confirm(`Delete ${lead.first_name} ${lead.last_name}'s lead profile?`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteLead(lead.id, activeToken);
      setLeads((current) => current.filter((item) => item.id !== lead.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete lead');
    }
  };

  const stats = useMemo(() => {
    const pending = leads.filter((lead) => lead.status === 'PENDING').length;
    const reachedOut = leads.filter((lead) => lead.status === 'REACHED_OUT').length;
    return { total: leads.length, pending, reachedOut };
  }, [leads]);

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">Alma</div>
        <div className="topbar-actions">
          <a href="/" className="link-button">
            Public intake
          </a>
          {isAuthenticated ? (
            <button className="ghost-button" onClick={handleSignOut}>
              Sign out
            </button>
          ) : null}
        </div>
      </header>

      <main className="admin-shell">
        {!isAuthenticated ? (
          <section className="panel admin-card">
            <h1>Internal access</h1>
            {status === 'loading' || googleAuthEnabled === null ? (
              <p className="inline-caption">Checking internal access…</p>
            ) : null}
            {googleAuthEnabled ? (
              <>
                <p className="inline-caption">Sign in with your approved Google account to review leads.</p>
                <button className="primary-button" onClick={() => void signIn('google')}>
                  Sign in with Google
                </button>
              </>
            ) : null}
            {googleAuthEnabled === false ? (
              <details className="fallback-auth" open>
                <summary>Use local token fallback</summary>
                <p className="inline-caption">Google OAuth is not configured locally. Reviewer default: change-me.</p>
                <div className="token-box">
                  <input
                    type="password"
                    value={fallbackToken}
                    onChange={(event) => setFallbackToken(event.target.value)}
                    placeholder="Internal token"
                  />
                  <button className="primary-button" onClick={handleFallbackContinue}>
                    Continue
                  </button>
                </div>
              </details>
            ) : null}
            {error ? <div className="error-box dashboard-error">{error}</div> : null}
          </section>
        ) : (
          <>
            <section className="panel admin-card">
              <div className="dashboard-header">
                <div>
                  <h1 className="dashboard-title">Lead dashboard</h1>
                  <p className="inline-caption dashboard-subtitle">
                    {signedInEmail ? `Signed in as ${signedInEmail}` : 'Using local token fallback'}
                  </p>
                </div>
                <button className="secondary-button" onClick={handleSignOut}>
                  Sign out
                </button>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Total leads</div>
                  <div className="stat-value">{stats.total}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Pending</div>
                  <div className="stat-value">{stats.pending}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Reached out</div>
                  <div className="stat-value">{stats.reachedOut}</div>
                </div>
              </div>

              {error ? <div className="error-box dashboard-error">{error}</div> : null}
            </section>

            <section className="panel admin-card">
              {loading ? <p className="inline-caption">Loading leads…</p> : null}
              {!loading && leads.length === 0 ? (
                <div className="empty-state">No leads yet. New submissions will appear here.</div>
              ) : null}
              {!loading && leads.length > 0 ? (
                <div className="table-shell">
                  <table className="lead-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Resume</th>
                        <th>Status</th>
                        <th>Submitted</th>
                        <th>Reached out</th>
                        <th className="row-delete-heading" aria-label="Delete lead" />
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map((lead) => (
                        <tr key={lead.id}>
                          <td>{`${lead.first_name} ${lead.last_name}`}</td>
                          <td>{lead.email}</td>
                          <td>
                            <button className="resume-link" onClick={() => handleDownloadResume(lead)}>
                              {lead.resume_original_filename}
                            </button>
                          </td>
                          <td>
                            <div className="status-actions">
                              {lead.status === 'PENDING' ? (
                                <button
                                  type="button"
                                  className="status-button status-button-pending"
                                  onClick={() => void handleStatusChange(lead)}
                                  aria-label={`Mark ${lead.first_name} ${lead.last_name} as reached out`}
                                  title="Mark this lead as reached out"
                                >
                                  PENDING
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="status-button status-button-reached"
                                  onClick={() => void handleStatusChange(lead)}
                                  title="Move this lead back to pending"
                                >
                                  REACHED OUT
                                </button>
                              )}
                              <button
                                type="button"
                                className="send-email-button"
                                onClick={() => void handleSendEmail(lead)}
                                disabled={sendingEmailId === lead.id}
                              >
                                {sendingEmailId === lead.id ? 'Sending…' : 'Send email'}
                              </button>
                              {emailFeedback?.leadId === lead.id ? (
                                <span className={`email-feedback email-feedback-${emailFeedback.kind}`} role="status">
                                  {emailFeedback.message}
                                </span>
                              ) : null}
                            </div>
                          </td>
                          <td>{new Date(lead.created_at).toLocaleDateString()}</td>
                          <td>{lead.reached_out_at ? new Date(lead.reached_out_at).toLocaleDateString() : '—'}</td>
                          <td>
                            <button
                              type="button"
                              className="icon-button danger-button"
                              onClick={() => handleDeleteLead(lead)}
                              aria-label={`Delete ${lead.first_name} ${lead.last_name}`}
                              title={`Delete ${lead.first_name} ${lead.last_name}`}
                            >
                              <svg aria-hidden="true" viewBox="0 0 24 24" className="icon">
                                <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm1 7h2v8h-2v-8Zm4 0h2v8h-2v-8ZM7 9h10l-1 12H8L7 9Z" />
                              </svg>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
