const state = {
  userId: null,
  users: [],
  properties: [],
};

const enums = {
  category: ["fontaneria", "electricidad", "cerraduras", "limpieza", "danos", "climatizacion", "ascensor", "seguridad", "otros"],
  priority: ["baja", "media", "alta", "urgente"],
  origin: ["inquilino", "propietario", "administrador", "inspeccion", "mantenimiento_preventivo"],
};

const $ = (id) => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.style.display = "block";
  setTimeout(() => (el.style.display = "none"), 2400);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", "X-User-Id": String(state.userId), ...(options.headers || {}) };
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Error ${res.status}`);
  }
  return res.json();
}

function renderEnumSelect(id, values) {
  $(id).innerHTML = values.map((v) => `<option value="${v}">${v}</option>`).join("");
}

function renderMetaSelectors() {
  $("userId").innerHTML = state.users.map((u) => `<option value="${u.id}">${u.full_name} (${u.role})</option>`).join("");
  $("propertySelect").innerHTML = state.properties.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
}

function renderDashboard(data) {
  $("dashboard").innerHTML = `
    <h2>Resumen</h2>
    <div class="stats">
      <div class="stat"><strong>${data.open_incidents}</strong><br>Abiertas</div>
      <div class="stat"><strong>${data.urgent_incidents}</strong><br>Urgentes</div>
      <div class="stat"><strong>${data.overdue_incidents}</strong><br>Vencidas</div>
      <div class="stat"><strong>${data.average_resolution_days}</strong><br>Días resolución</div>
    </div>
  `;
}

function renderIncidents(incidents) {
  $("incidents").innerHTML = incidents
    .map(
      (i) => `<article class="incident">
      <div class="row"><h3>#${i.id} · ${i.title}</h3><span class="badge">${i.status}</span></div>
      <p>${i.description}</p>
      <div class="row">
        <span class="badge">Prioridad: ${i.priority}</span>
        <span>Vence: ${i.due_date || "-"}</span>
        <span>Asignado: ${i.assigned_to_id || "-"}</span>
      </div>
    </article>`
    )
    .join("");
}

async function loadMetaAndData() {
  const meta = await api("/incidents/meta");
  state.users = meta.users;
  state.properties = meta.properties;
  renderMetaSelectors();
  state.userId = Number($("userId").value || meta.users[0]?.id);
  $("userId").value = String(state.userId);
  await refreshData();
}

async function refreshData() {
  if (!state.userId) return;
  const [dashboard, incidents] = await Promise.all([api("/incidents/dashboard/summary"), api("/incidents")]);
  renderDashboard(dashboard);
  renderIncidents(incidents);
}

function bindEvents() {
  $("userId").addEventListener("change", async (e) => {
    state.userId = Number(e.target.value);
    await refreshData();
  });

  $("reloadBtn").addEventListener("click", refreshData);

  $("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const payload = {
      title: form.get("title"),
      description: form.get("description"),
      opened_at: form.get("opened_at"),
      property_id: Number(form.get("property_id")),
      category: form.get("category"),
      priority: form.get("priority"),
      origin: form.get("origin"),
      attachments: [],
    };

    try {
      await api("/incidents", { method: "POST", body: JSON.stringify(payload) });
      e.target.reset();
      toast("Incidencia creada");
      await refreshData();
    } catch (err) {
      toast(err.message);
    }
  });
}

async function init() {
  renderEnumSelect("categorySelect", enums.category);
  renderEnumSelect("prioritySelect", enums.priority);
  renderEnumSelect("originSelect", enums.origin);
  bindEvents();

  state.userId = 2;
  try {
    await loadMetaAndData();
  } catch (err) {
    toast(err.message + ". Ejecuta seed y usa usuario válido.");
  }
}

init();
