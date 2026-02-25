import React, { useState } from "react";

import { adminLogin } from "../lib/api";
import { saveAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";

export function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit() {
    try {
      const token = await adminLogin(username, password);
      saveAdminToken(token.access_token);
      navigateTo("/admin");
    } catch {
      setError("Неверный логин или пароль");
    }
  }

  return (
    <main className="page">
      <section className="panel form-grid" aria-label="форма входа в админку">
        <h1>Вход в админку</h1>
        <label htmlFor="admin-username">Логин</label>
        <input id="admin-username" value={username} onChange={(event) => setUsername(event.target.value)} />

        <label htmlFor="admin-password">Пароль</label>
        <input
          id="admin-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {error ? <p role="alert">{error}</p> : null}

        <button type="button" onClick={() => void submit()}>
          Войти
        </button>
      </section>
    </main>
  );
}
