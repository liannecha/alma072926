'use client';

import { ChangeEvent, FormEvent, useState } from 'react';
import { createLead } from '../lib/api';

export default function HomePage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [resume, setResume] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setResume(file);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('first_name', firstName);
      formData.append('last_name', lastName);
      formData.append('email', email);
      if (resume) {
        formData.append('resume', resume);
      }

      await createLead(formData);
      setSuccess('Your lead was submitted successfully. Alma’s team will review it shortly.');
      setFirstName('');
      setLastName('');
      setEmail('');
      setResume(null);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit lead');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">Alma</div>
        <div className="topbar-actions">
          <a href="/admin" className="link-button">
            Internal Dashboard
          </a>
        </div>
      </header>

      <main className="hero-grid">
        <section className="panel intro-panel">
          <h1>Submit your profile</h1>
          <p>
            Share your information and resume so Alma’s team can review your case.
          </p>
          <p className="inline-caption">
            We will keep your submission simple and secure. New leads arrive as PENDING until an internal team member marks them reached out.
          </p>
        </section>

        <section className="panel form-panel">
          <form className="form-grid" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="first_name">First name</label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                required
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
              />
            </div>

            <div className="field">
              <label htmlFor="last_name">Last name</label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                required
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
              />
            </div>

            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="field">
              <label htmlFor="resume">Resume / CV</label>
              <input
                id="resume"
                name="resume"
                type="file"
                accept=".pdf,.doc,.docx"
                required
                onChange={handleFileChange}
              />
              <span className="inline-caption">
                {resume ? `Selected file: ${resume.name}` : 'Accepted formats: PDF, DOC, DOCX'}
              </span>
            </div>

            {error ? <div className="error-box">{error}</div> : null}
            {success ? <div className="success-box">{success}</div> : null}

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting…' : 'Submit profile'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
