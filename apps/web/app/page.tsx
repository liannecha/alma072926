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
      setSuccess('Your information was submitted successfully. Alma’s team will review it shortly.');
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
        <div className="brand">alma</div>
        <div className="topbar-actions">
          <a href="/admin" className="link-button">
            Internal dashboard
          </a>
        </div>
      </header>

      <main className="intake-stage">
        <div className="intake-grid">
          <section className="intro-panel">
            <div className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              GET STARTED
            </div>
            <h1>Submit your profile</h1>
            <p className="testimonial">Share your information and resume so Alma’s team can review your submission.</p>
          </section>

          <section className="form-panel" aria-label="Consultation request form">
            <div className="form-card">
              <div className="form-intro">
                <h2>Just provide a few details, and we'll get you started.</h2>
                <p>Required fields*</p>
              </div>

              <form className="form-grid" onSubmit={handleSubmit}>
                <div className="name-fields">
                  <div className="field">
                    <label className="sr-only" htmlFor="first_name">
                      First name
                    </label>
                    <input
                      id="first_name"
                      name="first_name"
                      type="text"
                      placeholder="First name*"
                      required
                      value={firstName}
                      onChange={(event) => setFirstName(event.target.value)}
                    />
                  </div>

                  <div className="field">
                    <label className="sr-only" htmlFor="last_name">
                      Last name
                    </label>
                    <input
                      id="last_name"
                      name="last_name"
                      type="text"
                      placeholder="Last name*"
                      required
                      value={lastName}
                      onChange={(event) => setLastName(event.target.value)}
                    />
                  </div>
                </div>

                <div className="field">
                  <label className="sr-only" htmlFor="email">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="Email*"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>

                <div className="field">
                  <label className="sr-only" htmlFor="resume">
                    Resume or CV
                  </label>
                  <label className="upload-control" htmlFor="resume">
                    <span>{resume ? resume.name : 'Upload resume or CV'}</span>
                    <span className="upload-helper">Max file size 10MB.</span>
                  </label>
                  <input
                    className="sr-only"
                    id="resume"
                    name="resume"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    required
                    onChange={handleFileChange}
                  />
                </div>

                {error ? <div className="error-box">{error}</div> : null}
                {success ? <div className="success-box">{success}</div> : null}

                <button className="primary-button intake-submit" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Submitting…' : 'Submit'}
                </button>
              </form>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
