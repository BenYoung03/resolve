  /* ============================================================
   STATE
   ============================================================ */
      let currentUser = null;
      let currentPage = "auth";
      let activeFilter = "all";
      let deleteCallback = null;
      let editRoleIdx = null;

      const TICKETS = [
        {
          id: 1,
          title: "Internet Connectivity Problem",
          priority: "high",
          status: "open",
          created: "03/02/2026",
          agent: "Birat",
          client: "Monica",
          category: "Networking",
          description:
            "My WiFi keeps dropping every few minutes. I have tried restarting the router but the problem persists.",
        },
        {
          id: 2,
          title: "Laptop Not Working",
          priority: "medium",
          status: "open",
          created: "03/02/2026",
          agent: "",
          client: "Monica",
          category: "Maintenance",
          description:
            "My laptop keeps restarting randomly many times a day. Can you please look into it?",
        },
        {
          id: 3,
          title: "Software Installation Help",
          priority: "low",
          status: "closed",
          created: "02/28/2026",
          agent: "Cameron",
          client: "Gavin",
          category: "Software",
          description: "Need help installing Photoshop on my workstation.",
        },
        {
          id: 4,
          title: "Password Reset Request",
          priority: "medium",
          status: "open",
          created: "03/01/2026",
          agent: "Richard",
          client: "John",
          category: "Account",
          description: "User forgot their Active Directory password.",
        },
      ];

      const USERS = [
        { name: "Richard", email: "richard@richard.com", role: "agent" },
        { name: "Cameron", email: "cameron@cameron.com", role: "agent" },
        { name: "admin", email: "admin@admin.com", role: "admin" },
      ];

      const CLIENTS = [
        { name: "Monica", email: "monica@monica.com", phone: "555-1234" },
        { name: "Gavin", email: "gavin@gavin.com", phone: "555-5678" },
        { name: "John Doe", email: "john@doe.com", phone: "555-9012" },
      ];

      const ROLES = [
        {
          name: "Tester",
          status: "active",
          perms: ["Read Issue", "Comment Issue"],
        },
        {
          name: "Manager",
          status: "inactive",
          perms: [
            "Create Issue",
            "Read Issue",
            "Update Issue",
            "Assign Issue",
            "Read Role",
          ],
        },
      ];

      let currentTicketId = null;

      /* ============================================================
   AUTH
   ============================================================ */
      function doLogin(e) {
        e.preventDefault();
        const role = document.getElementById("login-role").value;
        const email = document.getElementById("login-email").value;
        const name = email.split("@")[0];
        currentUser = { name, email, role };

        // Update sidebar
        document.getElementById("sidebar-username").textContent = name;
        const badgeEl = document.getElementById("sidebar-role-badge");
        badgeEl.textContent = role.charAt(0).toUpperCase() + role.slice(1);
        badgeEl.className = "sidebar-role-badge role-" + role;
        document.getElementById("topbar-username").textContent = name;
        document.getElementById("profile-name").value = name;
        document.getElementById("profile-email").value = email;
        document.getElementById("profile-role-display").textContent =
          role.charAt(0).toUpperCase() + role.slice(1);

        // Show/hide admin-only nav items
        document.querySelectorAll(".admin-only").forEach((el) => {
          el.style.display = role === "admin" ? "" : "none";
        });

        // Adjust "New Issue" label
        document.getElementById("new-ticket-label").textContent =
          role === "client" ? "New Ticket" : "New Issue";

        document.getElementById("sidebar").classList.remove("hidden");
        document.getElementById("main").classList.remove("full-width");
        navigate("dashboard");
        showToast("Welcome back, " + name + "!", "success");
      }

      function doRegister(e) {
        e.preventDefault();
        showToast("Account created! Please log in.", "success");
        e.target.reset();
      }

      function logout() {
        currentUser = null;
        document.getElementById("sidebar").classList.add("hidden");
        document.getElementById("main").classList.add("full-width");
        navigate("auth");
        showToast("Logged out.", "info");
      }

      /* ============================================================
   NAVIGATION
   ============================================================ */
      function navigate(page) {
        // Hide all pages
        document
          .querySelectorAll(".page")
          .forEach((p) => p.classList.remove("active"));

        // Show target
        const el = document.getElementById("page-" + page);
        if (!el) return;
        el.classList.add("active");

        // Auth page full-width
        if (page === "auth" || page === "guest-ticket") {
          document.getElementById("main").classList.add("full-width");
          document.getElementById("topbar").style.display = "none";
        } else {
          if (currentUser)
            document.getElementById("main").classList.remove("full-width");
          document.getElementById("topbar").style.display = "";
        }

        // Update active nav item
        document.querySelectorAll(".nav-item[data-page]").forEach((item) => {
          item.classList.toggle("active", item.dataset.page === page);
        });

        // Update topbar title
        const titles = {
          dashboard: "Dashboard",
          users: "Internal Users",
          clients: "Clients",
          roles: "Roles & Permissions",
          profile: "Profile",
          settings: "Settings",
          "ticket-detail": "Ticket Detail",
          "guest-ticket": "Submit a Ticket",
        };
        document.getElementById("topbar-title").textContent =
          titles[page] || "Resolve";

        currentPage = page;

        // Init page-specific content
        if (page === "dashboard") renderTicketTable();
        if (page === "users") renderUsersTable();
        if (page === "clients") renderClientsTable();
        if (page === "roles") renderRolesTable();
      }

      /* ============================================================
   DASHBOARD / TICKETS
   ============================================================ */
      function renderTicketTable(filter) {
        filter = filter || activeFilter;
        const tbody = document.getElementById("ticket-table-body");
        const visible =
          filter === "all"
            ? TICKETS
            : TICKETS.filter((t) => t.status === filter);

        // Update stats
        document.getElementById("stat-open").textContent = TICKETS.filter(
          (t) => t.status === "open",
        ).length;
        document.getElementById("stat-closed").textContent = TICKETS.filter(
          (t) => t.status === "closed",
        ).length;
        document.getElementById("stat-unassigned").textContent = TICKETS.filter(
          (t) => !t.agent,
        ).length;

        if (!visible.length) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:32px; color:var(--text-dim);">No tickets found.</td></tr>`;
          return;
        }

        tbody.innerHTML = visible
          .map(
            (t) => `
    <tr onclick="openTicket(${t.id})">
      <td>#${t.id}</td>
      <td>${t.title}</td>
      <td><span class="badge badge-${t.priority}">${t.priority}</span></td>
      <td><span class="badge badge-${t.status === "open" ? "open" : "closed"}">${t.status}</span></td>
      <td>${t.created}</td>
      <td>${t.agent ? t.agent : '<span class="text-muted">Unassigned</span>'}</td>
    </tr>
  `,
          )
          .join("");
      }

      function filterTickets(status) {
        activeFilter = status;
        document
          .querySelectorAll(".tab-btn")
          .forEach((b) => b.classList.remove("active"));
        renderTicketTable(status);
        if (currentPage !== "dashboard") navigate("dashboard");
      }

      function switchTab(btn, status) {
        document
          .querySelectorAll(".tab-btn")
          .forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = status;
        renderTicketTable(status);
      }

      function openTicket(id) {
        const t = TICKETS.find((x) => x.id === id);
        if (!t) return;
        currentTicketId = id;

        document.getElementById("td-id").textContent = "#" + t.id;
        document.getElementById("td-title").textContent = t.title;
        document.getElementById("td-description").textContent = t.description;
        document.getElementById("td-client-badge").textContent = t.client;
        document.getElementById("td-status-badge").textContent =
          t.status === "open" ? "Open Issue" : "Closed Issue";
        document.getElementById("td-status-badge").className =
          "badge " + (t.status === "open" ? "badge-open" : "badge-closed");
        document.getElementById("td-category-badge").textContent = t.category;
        document.getElementById("td-assigned").textContent =
          t.agent || "Unassigned";
        document.getElementById("td-priority").textContent = t.priority;
        document.getElementById("td-priority").className =
          "badge badge-" + t.priority;
        document.getElementById("td-status").textContent = t.status;
        document.getElementById("td-status").className =
          "badge " + (t.status === "open" ? "badge-open" : "badge-closed");
        document.getElementById("td-category").textContent = t.category;
        document.getElementById("td-created").textContent = t.created;
        document.getElementById("td-client-name").textContent = t.client;
        document.getElementById("td-comments-list").innerHTML = "";

        navigate("ticket-detail");
      }

      function closeTicket() {
        if (!currentTicketId) return;
        const t = TICKETS.find((x) => x.id === currentTicketId);
        if (!t) return;
        t.status = "closed";
        document.getElementById("td-status-badge").textContent = "Closed Issue";
        document.getElementById("td-status-badge").className =
          "badge badge-closed";
        document.getElementById("td-status").textContent = "closed";
        document.getElementById("td-status").className = "badge badge-closed";
        showToast("Ticket #" + t.id + " closed.", "success");
      }

      function addComment() {
        const input = document.getElementById("td-comment-input");
        const text = input.value.trim();
        if (!text) return;
        const list = document.getElementById("td-comments-list");
        const now = new Date().toLocaleString();
        const el = document.createElement("div");
        el.className = "activity-entry";
        el.innerHTML = `<strong>${currentUser ? currentUser.name : "User"}</strong> commented at ${now}: ${text}`;
        list.appendChild(el);
        input.value = "";
        showToast("Comment added.", "success");
      }

      function assignAgent() {
        const sel = document.getElementById("assign-agent-select").value;
        if (!currentTicketId) return;
        const t = TICKETS.find((x) => x.id === currentTicketId);
        if (t) {
          t.agent = sel || "";
          document.getElementById("td-assigned").textContent =
            sel || "Unassigned";
        }
        closeModal("modal-assign-ticket");
        showToast(sel ? "Assigned to " + sel : "Ticket unassigned.", "info");
      }

      function createTicket(e) {
        e.preventDefault();
        const newId = TICKETS.length + 1;
        TICKETS.push({
          id: newId,
          title: e.target.querySelector("input[type=text]").value,
          priority: e.target.querySelector("select:last-of-type").value,
          status: "open",
          created: new Date().toLocaleDateString("en-CA").replace(/-/g, "/"),
          agent: "",
          client: "",
          category: "Other",
          description: e.target.querySelector("textarea").value,
        });
        closeModal("modal-new-ticket");
        e.target.reset();
        renderTicketTable();
        showToast("Ticket #" + newId + " created!", "success");
      }

      /* ============================================================
   USERS TABLE
   ============================================================ */
      function renderUsersTable(filter) {
        const tbody = document.getElementById("users-table-body");
        const list = filter
          ? USERS.filter(
              (u) =>
                u.name.toLowerCase().includes(filter) ||
                u.email.toLowerCase().includes(filter),
            )
          : USERS;
        tbody.innerHTML = list
          .map(
            (u, i) => `
    <tr>
      <td>${u.name}</td>
      <td>${u.email}</td>
      <td><span class="badge ${u.role === "admin" ? "badge-open" : "badge-inprogress"}">${u.role}</span></td>
      <td>
        <div class="flex gap-8">
          <button class="btn btn-ghost btn-sm" onclick="openResetUserPw('${u.name}')">Reset PW</button>
          <button class="btn btn-danger btn-sm" onclick="confirmDeleteItem('${u.name}', 'user', ${i})">Delete</button>
        </div>
      </td>
    </tr>
  `,
          )
          .join("");
      }

      function filterUsers(val) {
        renderUsersTable(val.toLowerCase());
      }

      function addUser(e) {
        e.preventDefault();
        const inputs = e.target.querySelectorAll("input");
        USERS.push({
          name: inputs[0].value,
          email: inputs[1].value,
          role: document.getElementById("add-user-role").value,
        });
        closeModal("modal-add-user");
        e.target.reset();
        renderUsersTable();
        showToast("User created!", "success");
      }

      function openResetUserPw(name) {
        document.getElementById("reset-user-name").textContent = name;
        document.getElementById("reset-user-pw-input").value = "";
        openModal("modal-reset-user-pw");
      }

      function doResetUserPw() {
        closeModal("modal-reset-user-pw");
        showToast("Password reset successfully.", "success");
      }

      /* ============================================================
   CLIENTS TABLE
   ============================================================ */
      function renderClientsTable(filter) {
        const tbody = document.getElementById("clients-table-body");
        const list = filter
          ? CLIENTS.filter((c) => c.name.toLowerCase().includes(filter))
          : CLIENTS;
        tbody.innerHTML = list
          .map(
            (c, i) => `
    <tr>
      <td>${c.name}</td>
      <td>${c.email}</td>
      <td>${c.phone}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="confirmDeleteItem('${c.name}', 'client', ${i})">Delete</button>
      </td>
    </tr>
  `,
          )
          .join("");
      }

      function filterClients(val) {
        renderClientsTable(val.toLowerCase());
      }

      function addClient(e) {
        e.preventDefault();
        const inputs = e.target.querySelectorAll("input");
        CLIENTS.push({
          name: inputs[0].value,
          email: inputs[1].value,
          phone: inputs[2].value || "—",
        });
        closeModal("modal-new-client");
        e.target.reset();
        renderClientsTable();
        showToast("Client registered!", "success");
      }

      function copyGuestURL() {
        const url = window.location.href.split("?")[0] + "?page=guest-ticket";
        navigator.clipboard.writeText(url).catch(() => {});
        showToast("Guest ticket URL copied!", "info");
      }

      /* ============================================================
   ROLES TABLE
   ============================================================ */
      function renderRolesTable() {
        const tbody = document.getElementById("roles-table-body");
        tbody.innerHTML = ROLES.map(
          (r, i) => `
    <tr>
      <td>${r.name}</td>
      <td><span style="font-size:11px; color:var(--text-muted);">${r.perms.slice(0, 3).join(", ")}${r.perms.length > 3 ? " …" : ""}</span></td>
      <td><span class="badge badge-${r.status}">${r.status}</span></td>
      <td>
        <div class="flex gap-8">
          <button class="btn btn-ghost btn-sm" onclick="openEditRole(${i})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="confirmDeleteItem('${r.name}', 'role', ${i})">Delete</button>
        </div>
      </td>
    </tr>
  `,
        ).join("");
      }

      function toggleAllRoles(active) {
        ROLES.forEach((r) => (r.status = active ? "active" : "inactive"));
        renderRolesTable();
        showToast(
          active ? "All roles enabled." : "All roles disabled.",
          "info",
        );
      }

      function openRoleWizard() {
        document.getElementById("role-name-input").value = "";
        document
          .querySelectorAll(".perm-issue, .perm-role")
          .forEach((c) => (c.checked = false));
        populateWizardUsers();
        openModal("modal-role-wizard-1");
      }

      function roleWizardNext() {
        const name = document.getElementById("role-name-input").value.trim();
        if (!name) {
          showToast("Please enter a role name.", "error");
          return;
        }
        closeModal("modal-role-wizard-1");
        openModal("modal-role-wizard-2");
      }

      function roleWizardBack() {
        closeModal("modal-role-wizard-2");
        openModal("modal-role-wizard-1");
      }

      function populateWizardUsers() {
        const grid = document.getElementById("wizard-user-list");
        grid.innerHTML = USERS.map(
          (u, i) => `
    <label class="user-check-item">
      <input type="checkbox" style="accent-color:var(--teal);" data-uid="${i}">
      ${u.email}
    </label>
  `,
        ).join("");
      }

      function filterWizardUsers(val) {
        const grid = document.getElementById("wizard-user-list");
        grid.querySelectorAll(".user-check-item").forEach((item) => {
          item.style.display = item.textContent
            .toLowerCase()
            .includes(val.toLowerCase())
            ? ""
            : "none";
        });
      }

      function createRole() {
        const name = document.getElementById("role-name-input").value.trim();
        const perms = [
          ...document.querySelectorAll(
            ".perm-issue:checked, .perm-role:checked",
          ),
        ].map((c) => c.parentElement.textContent.trim());
        ROLES.push({ name, status: "active", perms });
        closeModal("modal-role-wizard-2");
        renderRolesTable();
        showToast('Role "' + name + '" created!', "success");
      }

      function openEditRole(idx) {
        editRoleIdx = idx;
        document.getElementById("edit-role-name-input").value = ROLES[idx].name;
        document.getElementById("edit-role-status").value = ROLES[idx].status;
        openModal("modal-edit-role");
      }

      function saveEditRole() {
        if (editRoleIdx === null) return;
        ROLES[editRoleIdx].name = document
          .getElementById("edit-role-name-input")
          .value.trim();
        ROLES[editRoleIdx].status =
          document.getElementById("edit-role-status").value;
        closeModal("modal-edit-role");
        renderRolesTable();
        showToast("Role updated!", "success");
      }

      function selectAllPerms(type, checked) {
        document
          .querySelectorAll(".perm-" + type)
          .forEach((c) => (c.checked = checked));
      }

      /* ============================================================
   DELETE CONFIRM
   ============================================================ */
      function confirmDeleteItem(name, type, idx) {
        document.getElementById("delete-target-name").textContent = name;
        deleteCallback = () => {
          if (type === "user") {
            USERS.splice(idx, 1);
            renderUsersTable();
          }
          if (type === "client") {
            CLIENTS.splice(idx, 1);
            renderClientsTable();
          }
          if (type === "role") {
            ROLES.splice(idx, 1);
            renderRolesTable();
          }
          showToast(name + " deleted.", "info");
        };
        openModal("modal-confirm-delete");
      }

      function confirmDelete() {
        if (deleteCallback) deleteCallback();
        deleteCallback = null;
        closeModal("modal-confirm-delete");
      }

      /* ============================================================
   PROFILE / SETTINGS
   ============================================================ */
      function saveProfile(e) {
        e.preventDefault();
        const name = document.getElementById("profile-name").value;
        if (currentUser) currentUser.name = name;
        document.getElementById("sidebar-username").textContent = name;
        document.getElementById("topbar-username").textContent = name;
        showToast("Profile saved!", "success");
      }

      function changePassword(e) {
        e.preventDefault();
        e.target.reset();
        showToast("Password updated successfully!", "success");
      }

      /* ============================================================
   GUEST TICKET
   ============================================================ */
      function submitGuestTicket(e) {
        e.preventDefault();
        const id = "TKT-" + String(Math.floor(Math.random() * 9000) + 1000);
        document.getElementById("submitted-ticket-id").textContent =
          "Ticket #: " + id;
        openModal("modal-ticket-submitted");
        e.target.reset();
      }

      /* ============================================================
   MODAL HELPERS
   ============================================================ */
      function openModal(id) {
        document.getElementById(id).classList.add("open");
      }

      function closeModal(id) {
        document.getElementById(id).classList.remove("open");
      }

      // Close modal on overlay click
      document.querySelectorAll(".modal-overlay").forEach((overlay) => {
        overlay.addEventListener("click", function (e) {
          if (e.target === this) this.classList.remove("open");
        });
      });

      // Close modal on Escape
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          document
            .querySelectorAll(".modal-overlay.open")
            .forEach((m) => m.classList.remove("open"));
        }
      });

      /* ============================================================
   AUTH HELPERS
   ============================================================ */
      function sendReset() {
        closeModal("modal-forgot-pw");
        showToast("Reset link sent to your email.", "info");
      }

      /* ============================================================
   TOAST
   ============================================================ */
      function showToast(msg, type = "info") {
        const icons = { success: "✓", error: "✕", info: "ℹ" };
        const container = document.getElementById("toast-container");
        const el = document.createElement("div");
        el.className = "toast " + type;
        el.innerHTML = `<span>${icons[type] || "•"}</span><span>${msg}</span>`;
        container.appendChild(el);
        setTimeout(() => {
          el.style.opacity = "0";
          el.style.transform = "translateX(20px)";
          el.style.transition = "all 0.3s";
          setTimeout(() => el.remove(), 300);
        }, 3000);
      }

      /* ============================================================
   INIT
   ============================================================ */
      (function init() {
        // Sidebar hidden initially
        document.getElementById("sidebar").classList.add("hidden");
        document.getElementById("main").classList.add("full-width");
        document.getElementById("topbar").style.display = "none";

        // Show auth page
        navigate("auth");

        // Hide admin-only items until login
        document
          .querySelectorAll(".admin-only")
          .forEach((el) => (el.style.display = "none"));
      })();