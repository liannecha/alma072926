'use client';

import { useEffect, useMemo, useState } from 'react';
import { Lead, listLeads, markLeadReachedOut } from '../../lib/api';

const STORAGE_KEY = 'alma-internal-token';

export default function AdminPage() {
  const [token, setToken] = useState('');
  const [savedToken, setSavedToken] = useState('');
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEY) || '';
    setSavedToken(storedToken);
    setToken(storedToken);
    if (storedToken) {
      void loadLeads(storedToken);
    }
  }, []);

  const isAuthenticated = Boolean(savedToken);

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

  const handleContinue = async () => {
    const activeToken = token.trim();
    if (!activeToken) {
      setError('Enter your internal token');
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, activeToken);
    setSavedToken(activeToken);
    await loadLeads(activeToken);
  };

  const handleSignOut = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setSavedToken('');
    setToken('');
    setLeads([]);
    setError(null);
  };

  const handleMarkReachedOut = async (leadId: number) => {
    if (!savedToken) {
      return;
    }

    try {
      const updatedLead = await markLeadReachedOut(leadId, savedToken);
      setLeads((current) => current.map((lead) => (lead.id === leadId ? updatedLead : lead)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update lead');
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
            <p className="inline-caption">Enter the internal token to review leads. Local default: change-me.</p>
            <div className="token-box">
              <input
                type="password"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Internal token"
              />
              <button className="primary-button" onClick={handleContinue}>
                Continue
              </button>
            </div>
            {error ? <div className="error-box" style={{ marginTop: '0.9rem' }}>{error}</div> : null}
          </section>
        ) : (
          <>
            <section className="panel admin-card">
              <div className="token-box" style={{ justifyContent: 'space-between' }}>
                <div>
                  <h1 style={{ margin: 0 }}>Lead dashboard</h1>
                  <p className="inline-caption" style={{ marginTop: '0.25rem' }}>
                    Review incoming leads and mark when the team has reached out.
                  </p>
                </div>
                <button className="secondary-button" onClick={handleSignOut}>
                  Clear token
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
                          <td>{lead.resume_original_filename}</td>
                          <td>
                            <span className={`badge ${lead.status === 'PENDING' ? 'badge-pending' : 'badge-reached'}`}>
                              {lead.status === 'PENDING' ? 'PENDING' : 'REACHED OUT'}
                            </span>
                          </td>
                          <td>{new Date(lead.created_at).toLocaleDateString()}</td>
                          <td>{lead.reached_out_at ? new Date(lead.reached_out_at).toLocaleDateString() : '—'}</td>
                          <td>
                            {lead.status === 'PENDING' ? (
                              <button className="secondary-button" onClick={() => handleMarkReachedOut(lead.id)}>
                                Mark reached out
                              </button>
                            ) : (
                              <button className="ghost-button" disabled>
                                Reached out
                              </button>
                            )}
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
