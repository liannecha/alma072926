'use client';

import { signIn, signOut, useSession } from 'next-auth/react';
import { useEffect, useMemo, useState } from 'react';
import { Lead, deleteLead, downloadLeadResume, listLeads, markLeadReachedOut } from '../../lib/api';

const STORAGE_KEY = 'alma-internal-token';

export default function AdminPage() {
  const { data: session, status } = useSession();
  const [fallbackToken, setFallbackToken] = useState('');
  const [savedFallbackToken, setSavedFallbackToken] = useState('');
  const [googleAuthEnabled, setGoogleAuthEnabled] = useState<boolean | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
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

  const handleMarkReachedOut = async (leadId: number) => {
    if (!activeToken) {
      return;
    }

    try {
      const updatedLead = await markLeadReachedOut(leadId, activeToken);
      setLeads((current) => current.map((lead) => (lead.id === leadId ? updatedLead : lead)));
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
            {error ? <div className="error-box" style={{ marginTop: '0.9rem' }}>{error}</div> : null}
          </section>
        ) : (
          <>
            <section className="panel admin-card">
              <div className="token-box" style={{ justifyContent: 'space-between' }}>
                <div>
                  <h1 style={{ margin: 0 }}>Lead dashboard</h1>
                  <p className="inline-caption" style={{ marginTop: '0.25rem' }}>
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

              {error ? <div className="error-box" style={{ marginTop: '0.9rem' }}>{error}</div> : null}
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
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map((lead) => (
                        <tr key={lead.id}>
                          <td>{`${lead.first_name} ${lead.last_name}`}</td>
                          <td>{lead.email}</td>
                          <td>
                            <button className="ghost-button" onClick={() => handleDownloadResume(lead)}>
                              {lead.resume_original_filename}
                            </button>
                          </td>
                          <td>
                            <span className={`badge ${lead.status === 'PENDING' ? 'badge-pending' : 'badge-reached'}`}>
                              {lead.status === 'PENDING' ? 'PENDING' : 'REACHED OUT'}
                            </span>
                          </td>
                          <td>{new Date(lead.created_at).toLocaleDateString()}</td>
                          <td>{lead.reached_out_at ? new Date(lead.reached_out_at).toLocaleDateString() : '—'}</td>
                          <td>
                            <div className="token-box" style={{ gap: '0.5rem', justifyContent: 'flex-start' }}>
                              {lead.status === 'PENDING' ? (
                                <button className="secondary-button" onClick={() => handleMarkReachedOut(lead.id)}>
                                  Mark reached out
                                </button>
                              ) : (
                                <button className="ghost-button" disabled>
                                  Reached out
                                </button>
                              )}
                              <button className="ghost-button" onClick={() => handleDeleteLead(lead)}>
                                Delete
                              </button>
                            </div>
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
