import React, { useState } from "react";

import { adminLogin } from "../lib/api";
import { saveAdminToken } from "../lib/auth";

export function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit() {
    try {
      const token = await adminLogin(username, password);
      saveAdminToken(token.access_token);
      window.history.pushState({}, "", "/admin");
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <main className="page">
      <section className="panel form-grid" aria-label="admin login form">
        <h1>Admin login</h1>
        <label htmlFor="admin-username">Username</label>
        <input id="admin-username" value={username} onChange={(event) => setUsername(event.target.value)} />

        <label htmlFor="admin-password">Password</label>
        <input
          id="admin-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {error ? <p role="alert">{error}</p> : null}

        <button type="button" onClick={() => void submit()}>
          Login
        </button>
      </section>
    </main>
  );
}
