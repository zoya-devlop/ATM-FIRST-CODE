const state = {
  token: null,
  dashboard: null,
};

const loginForm = document.getElementById("login-form");
const loginStatus = document.getElementById("login-status");
const dashboardSection = document.getElementById("dashboard");
const refreshButton = document.getElementById("refresh-button");

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, { ...options, headers });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function badge(status) {
  const normalized = status.toLowerCase();
  let className = "badge";
  if (["scaling", "upgrading", "due", "provisioning"].includes(normalized)) {
    className += " warning";
  }
  if (["failed", "down"].includes(normalized)) {
    className += " danger";
  }
  return `<span class="${className}">${status}</span>`;
}

function renderList(targetId, items, mapper) {
  const target = document.getElementById(targetId);
  target.innerHTML = items.map(mapper).join("");
}

function populateProjectSelects(projects) {
  document.querySelectorAll('select[name="project_id"]').forEach((select) => {
    const current = select.value;
    select.innerHTML = projects
      .map((project) => `<option value="${project.id}">${project.name} (${project.region})</option>`)
      .join("");
    if (current) {
      select.value = current;
    }
  });
}

function renderDashboard(data) {
  state.dashboard = data;
  dashboardSection.classList.remove("hidden");

  const summaryGrid = document.getElementById("summary-grid");
  summaryGrid.innerHTML = [
    ["Projects", data.summary.projects],
    ["Instances", data.summary.instances],
    ["Clusters", data.summary.clusters],
    ["Buckets", data.summary.buckets],
    ["Healthy Projects", data.summary.healthy_projects],
    ["Monthly Cost", currency(data.summary.monthly_cost)],
  ]
    .map(
      ([label, value]) => `
        <article class="summary-card">
          <span class="muted">${label}</span>
          <strong>${value}</strong>
        </article>
      `
    )
    .join("");

  populateProjectSelects(data.projects);

  renderList(
    "projects-list",
    data.projects,
    (project) => `
      <article class="list-item">
        <strong>${project.name}</strong>
        <p>${project.region} | Owner ${project.owner_email}</p>
        <p>${badge(project.status)} | ${currency(project.monthly_cost)} / month</p>
      </article>
    `
  );

  renderList(
    "instances-list",
    data.instances,
    (instance) => `
      <article class="list-item">
        <strong>${instance.name}</strong>
        <p>${instance.region} | ${instance.vcpu} vCPU | ${instance.memory_gb}GB RAM</p>
        <p>${badge(instance.status)} | ${instance.public_ip}</p>
      </article>
    `
  );

  renderList(
    "clusters-list",
    data.clusters,
    (cluster) => `
      <article class="list-item">
        <strong>${cluster.name}</strong>
        <p>${cluster.region} | ${cluster.node_count} nodes | Kubernetes ${cluster.kubernetes_version}</p>
        <p>${badge(cluster.status)}</p>
      </article>
    `
  );

  renderList(
    "buckets-list",
    data.buckets,
    (bucketItem) => `
      <article class="list-item">
        <strong>${bucketItem.name}</strong>
        <p>${bucketItem.region} | ${bucketItem.size_gb}GB | ${bucketItem.object_count} objects</p>
      </article>
    `
  );

  renderList(
    "invoices-list",
    data.invoices,
    (invoice) => `
      <article class="list-item">
        <strong>${invoice.period}</strong>
        <p>${currency(invoice.amount)} | ${badge(invoice.status)}</p>
      </article>
    `
  );

  renderList(
    "events-list",
    data.events,
    (event) => `
      <article class="list-item">
        <strong>${event.actor}</strong>
        <p>${event.action} ${event.resource_type} <em>${event.resource_name}</em></p>
        <p>${new Date(event.created_at).toLocaleString()}</p>
      </article>
    `
  );
}

async function refreshDashboard() {
  const data = await api("/api/dashboard");
  renderDashboard(data);
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginStatus.textContent = "Signing in...";

  const formData = new FormData(loginForm);
  try {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    state.token = data.token;
    loginStatus.textContent = `Signed in as ${data.user.name}`;
    await refreshDashboard();
  } catch (error) {
    loginStatus.textContent = error.message;
  }
});

refreshButton.addEventListener("click", refreshDashboard);

async function handleCreate(formId, path, buildPayload) {
  const form = document.getElementById(formId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      await api(path, {
        method: "POST",
        body: JSON.stringify(buildPayload(formData)),
      });
      form.reset();
      await refreshDashboard();
    } catch (error) {
      alert(error.message);
    }
  });
}

handleCreate("project-form", "/api/projects", (formData) => ({
  name: formData.get("name"),
  region: formData.get("region"),
}));

handleCreate("instance-form", "/api/instances", (formData) => ({
  project_id: Number(formData.get("project_id")),
  name: formData.get("name"),
  region: formData.get("region"),
  vcpu: Number(formData.get("vcpu")),
  memory_gb: Number(formData.get("memory_gb")),
}));

handleCreate("cluster-form", "/api/clusters", (formData) => ({
  project_id: Number(formData.get("project_id")),
  name: formData.get("name"),
  region: formData.get("region"),
  node_count: Number(formData.get("node_count")),
  kubernetes_version: formData.get("kubernetes_version"),
}));

handleCreate("bucket-form", "/api/buckets", (formData) => ({
  project_id: Number(formData.get("project_id")),
  name: formData.get("name"),
  region: formData.get("region"),
}));
