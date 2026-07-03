// 1. Ab hum browser ki tijori (localStorage) se bhi token uthayenge!
const state = {
  token: localStorage.getItem('zoy_token') || null,
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

  // 2. Guard ko ID card (Token) dikhane ka logic
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

  // Agar user dashboard dekh raha hai, toh login form chupa do
  const heroPanel = document.querySelector('.hero-panel');
  if (heroPanel) heroPanel.style.display = 'none';

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

  // 🚀 FIXED INSTANCE LIST (Correct function name aur id passing)
  renderList(
    "instances-list",
    data.instances,
    (instance) => `
      <article class="list-item" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <strong>${instance.name}</strong>
          <p>${instance.region} | ${instance.vcpu} vCPU | ${instance.memory_gb}GB RAM</p>
          <p>${badge(instance.status)}</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button onclick="window.open('http://${instance.public_ip || '127.0.0.1'}', '_blank')" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid #38bdf8; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.3)'" onmouseout="this.style.background='rgba(56, 189, 248, 0.1)'">
            Open 🌍
          </button>
          
          <button onclick="viewZoyLogs('${instance.name}')" style="background: rgba(168, 85, 247, 0.1); color: #a855f7; border: 1px solid #a855f7; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.background='rgba(168, 85, 247, 0.3)'" onmouseout="this.style.background='rgba(168, 85, 247, 0.1)'">
            Logs 🖥️
          </button>

          <button onclick="deleteInstance('${instance.id}')" style="background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid #ef4444; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.background='rgba(239, 68, 68, 0.3)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.1)'">
            Delete 🗑️
          </button>
        </div>
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

    state.token = data.access_token;
    localStorage.setItem('zoy_token', data.access_token); 
    
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

// 4. JADOO: Agar pehle se token hai (Premium UI se login kiya ho), toh direct dashboard khol do!
if (state.token) {
    refreshDashboard().catch(() => {
        // Token expire ho gaya toh tijori saaf kar do
        localStorage.removeItem('zoy_token');
        state.token = null;
    });
}

// 🛡️ THE BULLETPROOF DELETE FUNCTION (SUDO PIN PROTECTED)
window.deleteInstance = async function(id) {
    console.log("Delete button clicked for ID:", id); 

    const enteredPin = prompt("⚠️ WARNING: You are about to DESTROY this server.\n\nEnter Admin PIN to confirm destruction:");

    if (!enteredPin) {
        alert("🛡️ Action Cancelled. Your server is safe!");
        return;
    }

    try {
        const response = await fetch(`/api/instances/${id}?pin=${enteredPin}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const data = await response.json();
            alert("✅ " + data.message);
            location.reload(); 
        } else {
            const errorData = await response.json();
            alert("❌ " + (errorData.detail || "Server request failed.")); 
        }
    } catch (error) {
        alert("Server Error: " + error);
    }
};

// 🖥️ THE PRO IN-PAGE MATRIX TERMINAL
window.viewZoyLogs = async function(instanceName) {
  try {
    const data = await api(`/api/instances/${instanceName}/logs`);
    
    const oldTerminal = document.getElementById('zoy-terminal-modal');
    if (oldTerminal) oldTerminal.remove();

    const terminalHTML = `
      <div id="zoy-terminal-modal" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(8px);">
        <div style="background: #0b0f19; border: 1px solid #32CD32; width: 80%; max-width: 900px; height: 70vh; border-radius: 12px; display: flex; flex-direction: column; box-shadow: 0 0 30px rgba(50, 205, 50, 0.2);">
          
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #1f2937; background: #111827; border-radius: 12px 12px 0 0;">
            <strong style="color: #94a3b8; font-family: monospace; font-size: 14px;">🟢 zoy-root@${instanceName}:~/logs</strong>
            <button onclick="document.getElementById('zoy-terminal-modal').remove()" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; border-radius: 8px; padding: 4px 12px; cursor: pointer; font-weight: bold; transition: 0.3s;" onmouseover="this.style.background='rgba(239, 68, 68, 0.4)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.2)'">Close</button>
          </div>
          
          <pre style="flex: 1; padding: 20px; color: #32CD32; font-family: 'Courier New', monospace; overflow-y: auto; margin: 0; font-size: 14px; white-space: pre-wrap;">${data.logs}</pre>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', terminalHTML);

  } catch (error) {
    alert("❌ Logs fetch karne mein error: " + error.message);
  }
};

// 🛍️ SCAN & GO: THE CHECKOUT PROCESS
window.processCheckout = async function(scannedBarcodes) {
    try {
        const response = await api("/api/checkout/", {
            method: "POST",
            body: JSON.stringify({ barcodes: scannedBarcodes }),
        });

        if (response.status === "success") {
            alert(`✅ Payment Successful! Token: ${response.security_exit_token}`);
        } else {
            alert("❌ Checkout failed: " + response.message);
        }
    } catch (error) {
        alert("Server error: " + error.message);
    }
};