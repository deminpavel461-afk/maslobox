(() => {
  window.__MASLOBOX_ADMIN_READY__ = true;
  const API = "/api/v1";
  const TOKEN_KEY = "maslobox_admin_token";
  const NEXT = {
    new: ["confirmed", "canceled"],
    confirmed: ["done", "canceled"],
    done: [],
    canceled: [],
  };

  const state = {
    token: localStorage.getItem(TOKEN_KEY) || "",
    page: 1,
    pageSize: 20,
    pages: 1,
    total: 0,
    points: [],
    items: [],
    current: null,
  };

  const loginView = document.getElementById("login-view");
  const appView = document.getElementById("app-view");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const tokenInput = document.getElementById("token-input");
  const filtersForm = document.getElementById("filters");
  const bookingsBody = document.getElementById("bookings-body");
  const metaLine = document.getElementById("meta-line");
  const pageLabel = document.getElementById("page-label");
  const prevPage = document.getElementById("prev-page");
  const nextPage = document.getElementById("next-page");
  const pointFilter = document.getElementById("point-filter");
  const dialog = document.getElementById("booking-dialog");
  const dialogTitle = document.getElementById("dialog-title");
  const dialogBody = document.getElementById("dialog-body");
  const dialogStatus = document.getElementById("dialog-status");
  const dialogComment = document.getElementById("dialog-comment");
  const dialogError = document.getElementById("dialog-error");
  const saveBooking = document.getElementById("save-booking");

  function authHeaders() {
    // X-Admin-Token — запасной путь: некоторые прокси Timeweb режут Authorization
    return {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${state.token}`,
      "X-Admin-Token": state.token,
    };
  }

  async function api(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text };
    }
    if (!res.ok) {
      const err = new Error("request_failed");
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function showLogin(message = "") {
    state.token = "";
    localStorage.removeItem(TOKEN_KEY);
    loginView.hidden = false;
    appView.hidden = true;
    loginError.hidden = !message;
    loginError.textContent = message;
  }

  function showApp() {
    loginView.hidden = true;
    appView.hidden = false;
  }

  function formatDate(value) {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function statusClass(status) {
    return `status status-${status}`;
  }

  function getFilters() {
    const data = new FormData(filtersForm);
    const params = new URLSearchParams();
    params.set("page", String(state.page));
    params.set("page_size", String(state.pageSize));
    for (const key of ["q", "status", "point_id", "date_from", "date_to"]) {
      const value = String(data.get(key) || "").trim();
      if (value) params.set(key, value);
    }
    return params;
  }

  async function loadPoints() {
    const res = await fetch(`${API}/points`, { headers: { Accept: "application/json" } });
    if (!res.ok) {
      const err = new Error("Не удалось загрузить точки");
      err.status = res.status;
      throw err;
    }
    const points = await res.json();
    state.points = points;
    pointFilter.innerHTML = '<option value="">Все</option>';
    for (const point of points) {
      const opt = document.createElement("option");
      opt.value = point.id;
      opt.textContent = `${point.name} — ${point.address}`;
      pointFilter.appendChild(opt);
    }
  }

  async function loadBookings() {
    bookingsBody.innerHTML = '<tr><td colspan="8" class="empty">Загрузка…</td></tr>';
    try {
      const data = await api(`/admin/bookings?${getFilters().toString()}`);
      state.items = data.items || [];
      state.total = data.meta.total;
      state.pages = Math.max(data.meta.pages || 1, 1);
      state.page = data.meta.page;
      metaLine.textContent = `Всего: ${state.total}`;
      pageLabel.textContent = `${state.page} / ${state.pages}`;
      prevPage.disabled = state.page <= 1;
      nextPage.disabled = state.page >= state.pages;

      if (!data.items.length) {
        bookingsBody.innerHTML = '<tr><td colspan="8" class="empty">Заявок нет</td></tr>';
        return;
      }

      bookingsBody.innerHTML = "";
      for (const item of data.items) {
        const tr = document.createElement("tr");
        const pointName = item.point ? item.point.name : "—";
        tr.innerHTML = `
          <td>#${item.id}</td>
          <td>${formatDate(item.created_at)}</td>
          <td>
            <span class="client-name">${escapeHtml(item.name)}</span>
            <span class="client-phone">${escapeHtml(item.phone)}</span>
          </td>
          <td>${escapeHtml(item.car_model)}</td>
          <td>${escapeHtml(pointName)}</td>
          <td>${escapeHtml(item.desired_datetime_raw || "—")}</td>
          <td><span class="${statusClass(item.status)}">${item.status}</span></td>
          <td><button type="button" class="btn btn-ghost" data-open="${item.id}">Открыть</button></td>
        `;
        bookingsBody.appendChild(tr);
      }
    } catch (err) {
      if (err.status === 401) {
        showLogin("Неверный ключ или сессия истекла");
        return;
      }
      bookingsBody.innerHTML = `<tr><td colspan="8" class="empty">Ошибка загрузки: ${escapeHtml(errorMessage(err))}</td></tr>`;
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function errorMessage(err) {
    if (err?.data?.detail) {
      if (typeof err.data.detail === "string") return err.data.detail;
      if (Array.isArray(err.data.detail)) {
        return err.data.detail.map((x) => x.message || JSON.stringify(x)).join("; ");
      }
    }
    return err?.message || "неизвестная ошибка";
  }

  function openDialog(item) {
    state.current = item;
    dialogTitle.textContent = `Заявка #${item.id}`;
    dialogError.hidden = true;
    dialogBody.innerHTML = `
      <div><strong>Клиент:</strong> ${escapeHtml(item.name)} · ${escapeHtml(item.phone)}</div>
      <div><strong>Авто:</strong> ${escapeHtml(item.car_model)}</div>
      <div><strong>Точка:</strong> ${escapeHtml(item.point ? item.point.name : "не указана")}</div>
      <div><strong>Желаемое время:</strong> ${escapeHtml(item.desired_datetime_raw || "—")}</div>
      <div><strong>Комментарий клиента:</strong> ${escapeHtml(item.comment || "—")}</div>
      <div><strong>Источник:</strong> ${escapeHtml(item.source)}</div>
      <div><strong>Создана:</strong> ${formatDate(item.created_at)}</div>
    `;

    const allowed = [item.status, ...(NEXT[item.status] || [])];
    dialogStatus.innerHTML = "";
    for (const status of allowed) {
      const opt = document.createElement("option");
      opt.value = status;
      opt.textContent = status;
      if (status === item.status) opt.selected = true;
      dialogStatus.appendChild(opt);
    }
    dialogStatus.disabled = (NEXT[item.status] || []).length === 0;
    dialogComment.value = item.admin_comment || "";
    dialog.showModal();
  }

  async function bootstrap() {
    if (!state.token) {
      showLogin();
      return;
    }
    showApp();
    try {
      await loadPoints();
      await loadBookings();
    } catch (err) {
      if (err.status === 401) showLogin("Неверный ключ администратора");
      else showLogin(errorMessage(err));
    }
  }

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const token = tokenInput.value.trim();
    if (!token) return;

    const btn = document.getElementById("login-btn");
    const prevLabel = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Вход…";
    loginError.hidden = true;
    state.token = token;

    try {
      // Сразу проверяем ключ через админский API
      await api("/admin/bookings?page=1&page_size=1");
      localStorage.setItem(TOKEN_KEY, token);
      showApp();
      await loadPoints();
      state.page = 1;
      await loadBookings();
    } catch (err) {
      state.token = "";
      localStorage.removeItem(TOKEN_KEY);
      loginView.hidden = false;
      appView.hidden = true;
      loginError.hidden = false;
      if (err.status === 401) {
        loginError.textContent = "Неверный ключ. Попробуйте change-me-admin-token или свой ADMIN_TOKEN.";
      } else if (err.status === 404) {
        loginError.textContent = "API не найден. Проверьте, что открыт адрес сайта Timeweb, а не локальный файл.";
      } else {
        loginError.textContent = errorMessage(err);
      }
    } finally {
      btn.disabled = false;
      btn.textContent = prevLabel;
    }
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    showLogin();
    tokenInput.value = "";
  });

  filtersForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    state.page = 1;
    await loadBookings();
  });

  document.getElementById("reset-filters").addEventListener("click", async () => {
    filtersForm.reset();
    state.page = 1;
    await loadBookings();
  });

  prevPage.addEventListener("click", async () => {
    if (state.page <= 1) return;
    state.page -= 1;
    await loadBookings();
  });

  nextPage.addEventListener("click", async () => {
    if (state.page >= state.pages) return;
    state.page += 1;
    await loadBookings();
  });

  bookingsBody.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-open]");
    if (!btn) return;
    const id = Number(btn.getAttribute("data-open"));
    const item = state.items.find((x) => x.id === id);
    if (item) openDialog(item);
  });

  saveBooking.addEventListener("click", async () => {
    if (!state.current) return;
    dialogError.hidden = true;
    const payload = {
      status: dialogStatus.value,
      admin_comment: dialogComment.value.trim() || null,
    };
    try {
      await api(`/admin/bookings/${state.current.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      dialog.close();
      await loadBookings();
    } catch (err) {
      dialogError.hidden = false;
      dialogError.textContent = errorMessage(err);
    }
  });

  bootstrap();
})();
