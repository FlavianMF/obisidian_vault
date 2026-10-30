// Keyboard-driven review (Operate mode). Vanilla JS: no build step, no dependencies.
(function () {
  "use strict";
  var SHORTCUTS = JSON.parse(document.getElementById("shortcuts").textContent);
  var app = document.getElementById("app");
  var stage = document.getElementById("stage");
  var overlay = document.getElementById("overlay");
  var query = JSON.parse(app.dataset.query || "{}");
  var VALIDATE_DELAY = 500;
  var inflight = false;
  var modal = null; // null | "editor" | "drop": while set, the triage keys are off
  var restoreTo = null;

  function card() { return document.getElementById("card"); }
  function $(id) { return document.getElementById(id); }

  function toast(message, kind) {
    var box = $("toasts");
    var el = document.createElement("div");
    el.className = "toast toast-" + (kind || "info");
    el.textContent = message;
    box.appendChild(el);
    setTimeout(function () { el.remove(); }, 4000);
  }

  function qs(extra) {
    var params = new URLSearchParams(query);
    Object.keys(extra || {}).forEach(function (k) { params.set(k, extra[k]); });
    return params.toString();
  }

  function setBusy(key, busy) {
    inflight = busy;
    app.classList.toggle("inflight", busy);
    var btn = document.querySelector('button[data-key="' + key + '"]');
    if (btn) { btn.classList.toggle("inflight", busy); }
  }

  function restoreFocus() {
    if (document.activeElement && document.activeElement !== document.body) { document.activeElement.blur(); }
    document.body.focus();
  }

  function errorText(data, status) {
    if (!data) { return "erro do servidor (" + status + ")"; }
    var text = data.detail || "erro " + status;
    if (data.errors && data.errors.length) { text += ": " + data.errors.join("; "); }
    if (data.findings && data.findings.length) { text += " [" + data.findings.join(", ") + "]"; }
    return text;
  }

  function send(path, body) {
    return fetch(path, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (data) { return { ok: r.ok, status: r.status, data: data }; });
    });
  }

  function refreshStats() {
    return fetch("/api/stats").then(function (r) { return r.ok ? r.json() : null; }).then(function (s) {
      if (!s) { return; }
      $("pending").textContent = s.pending + " pendentes";
      $("today-applied").textContent = s.today_applied;
      $("today-rejected").textContent = s.today_rejected;
    }).catch(function () {});
  }

  function load(extra) {
    return fetch("/ui/candidate?" + qs(extra)).then(function (r) {
      return r.text().then(function (html) { return { ok: r.ok, html: html }; });
    }).then(function (res) {
      stage.innerHTML = res.html;
      var c = card();
      $("pos").textContent = c.dataset.empty === "true" ? 0 : Number(c.dataset.offset) + 1;
      $("total").textContent = c.dataset.total || 0;
      return res.ok;
    });
  }

  function run(key, task) {
    if (inflight) { return; }
    setBusy(key, true);
    task().catch(function () { toast("erro do servidor", "error"); }).then(function () {
      setBusy(key, false);
      if (!modal) { restoreFocus(); }
    });
  }

  // A decision that went through: toast, show the next candidate, refresh the counters.
  function afterDecide(action, data) {
    var lines = String(data.message).trim().split("\n");
    toast(lines[lines.length - 1].trim(), action === "skip" ? "info" : "success");
    return load(data.next_candidate_id ? { id: data.next_candidate_id } : { offset: 0 }).then(refreshStats);
  }

  function decide(key, action, extra) {
    var c = card();
    if (!c || c.dataset.empty === "true") { toast("fila vazia", "info"); return; }
    run(key, function () {
      var body = Object.assign({ id: c.dataset.id, action: action }, extra || {});
      return send("/api/decide", body).then(function (res) {
        if (!res.ok) { toast(errorText(res.data, res.status), "error"); return; }
        return afterDecide(action, res.data);
      });
    });
  }

  function undo() {
    run("z", function () {
      return send("/api/undo", {}).then(function (res) {
        if (!res.ok) { toast(errorText(res.data, res.status), "error"); return; }
        toast(res.data.message, "info");
        return load({ id: res.data.id }).then(function (ok) {
          if (!ok) { return load({ offset: 0 }); }
        }).then(refreshStats);
      });
    });
  }

  function navigate(key, delta) {
    var c = card();
    var offset = Number(c.dataset.offset || 0), total = Number(c.dataset.total || 0);
    var target = offset + delta;
    if (c.dataset.empty === "true" || target < 0 || target >= total) {
      toast(delta < 0 ? "início da fila" : "fim da fila", "info");
      return;
    }
    run(key, function () { return load({ offset: target }); });
  }

  // ------------------------------------------------------------ modals
  function showAlert(id, text) {
    var box = $(id);
    box.textContent = text || "";
    box.hidden = !text;
  }

  function openOverlay(kind, node) {
    restoreTo = document.activeElement;
    overlay.replaceChildren(node);
    app.inert = true;
    modal = kind;
  }

  function closeModal() {
    overlay.replaceChildren();
    app.inert = false;
    modal = null;
    seq += 1; // a validation still in flight is stale now
    clearTimeout(timer);
    restoreTo = null;
    restoreFocus();
  }

  var seq = 0;
  var timer = null;

  // Validation without side effects: the server runs the same checks as a real decision (dry_run).
  function validate(body, statusId, alertId, onIssue) {
    var mine = ++seq;
    var chip = $(statusId);
    chip.textContent = "validando…";
    send("/api/decide", Object.assign({ dry_run: true }, body)).then(function (res) {
      if (mine !== seq || !chip.isConnected) { return; }
      if (res.ok) {
        chip.textContent = "válido";
        chip.className = "text-xs text-emerald-400";
        showAlert(alertId, "");
        if (onIssue) { onIssue(null); }
      } else {
        chip.textContent = "inválido";
        chip.className = "text-xs text-red-300";
        showAlert(alertId, errorText(res.data, res.status));
        if (onIssue) { onIssue(res.data); }
      }
    }).catch(function () {
      if (mine === seq && chip.isConnected) { chip.textContent = "não validado"; chip.className = "text-xs text-zinc-400"; }
    });
  }

  function schedule(fn) {
    clearTimeout(timer);
    timer = setTimeout(fn, VALIDATE_DELAY);
  }

  function editorValues() {
    var mode = document.querySelector('#ed-form input[name="mode"]:checked').value;
    var tags = $("ed-tags").value.split(",").map(function (t) { return t.trim(); }).filter(Boolean);
    var values = { id: $("editor").dataset.id, action: mode, title: $("ed-title").value, tags: tags, body: $("ed-body").value };
    if (mode === "absorb") { values.note = $("ed-note").value; }
    var because = $("ed-because").value.trim();
    if (because) { values.new_because = because; }
    return values;
  }

  function snapshot() {
    return JSON.stringify([$("ed-title").value, $("ed-tags").value, $("ed-body").value, $("ed-because").value]);
  }

  var editorSnap = "";
  var bodySnap = "";
  var prev = { mode: "save", note: "" };

  function revertChoice() {
    var radio = $("editor").querySelector('input[name="mode"][value="' + prev.mode + '"]');
    if (radio) { radio.checked = true; }
    if (prev.note) { $("ed-note").value = prev.note; }
  }

  function editorDirty() { return snapshot() !== editorSnap; }

  function validateEditor() {
    validate(editorValues(), "ed-status", "ed-alert", function (data) {
      var needs = !!(data && /new_because/.test(JSON.stringify(data)));
      $("ed-because-wrap").hidden = !needs && !$("ed-because").value;
    });
  }

  function bindEditor() {
    editorSnap = snapshot();
    bodySnap = $("ed-body").value;
    prev = { mode: document.querySelector('#ed-form input[name="mode"]:checked').value, note: $("ed-note").value };
    ["ed-title", "ed-tags", "ed-body", "ed-because"].forEach(function (id) {
      $(id).addEventListener("input", function () { schedule(validateEditor); });
    });
    document.querySelectorAll('#ed-form input[name="mode"]').forEach(function (radio) {
      radio.addEventListener("change", function () { reloadEditor(radio.value, ""); });
    });
    $("ed-note").addEventListener("change", function () { reloadEditor("absorb", $("ed-note").value); });
    $("ed-cancel").addEventListener("click", cancelEditor);
    $("ed-confirm").addEventListener("click", submitEditor);
    $("ed-title").focus();
    validateEditor();
  }

  function fetchEditor(id, mode, note) {
    var params = new URLSearchParams({ id: id });
    if (mode) { params.set("mode", mode); }
    if (note) { params.set("note", note); }
    return fetch("/ui/editor?" + params.toString()).then(function (r) {
      return r.text().then(function (html) {
        var tpl = document.createElement("template");
        tpl.innerHTML = html.trim();
        return { ok: r.ok, node: tpl.content.firstElementChild };
      });
    });
  }

  function openEditor() {
    var c = card();
    if (modal || inflight) { return; }
    if (!c || c.dataset.empty === "true") { toast("fila vazia", "info"); return; }
    fetchEditor(c.dataset.id, null, "").then(function (res) {
      if (!res.ok) { toast(res.node ? res.node.textContent.trim() : "erro do servidor", "error"); return; }
      openOverlay("editor", res.node);
      bindEditor();
    }).catch(function () { toast("erro do servidor", "error"); });
  }

  // Switching mode or target replaces the body: ask first when the body was edited; keep title, tags and reason.
  function reloadEditor(mode, note) {
    var id = $("editor").dataset.id;
    var edited = $("ed-body").value !== bodySnap;
    var keep = { title: $("ed-title").value, tags: $("ed-tags").value, because: $("ed-because").value };
    if (edited && !window.confirm("Trocar a ação recarrega o corpo e descarta as edições dele. Continuar?")) {
      revertChoice();
      return;
    }
    seq += 1;
    fetchEditor(id, mode, note).then(function (res) {
      if (!res.ok) {
        showAlert("ed-alert", res.node ? res.node.textContent.trim() : "erro do servidor");
        revertChoice();
        return;
      }
      overlay.replaceChildren(res.node);
      $("ed-title").value = keep.title;
      $("ed-tags").value = keep.tags;
      $("ed-because").value = keep.because;
      bindEditor();
    }).catch(function () { showAlert("ed-alert", "erro do servidor"); });
  }

  function cancelEditor() {
    if (editorDirty() && !window.confirm("Descartar edições não salvas?")) { return; }
    closeModal();
  }

  function submitEditor() {
    var confirmBtn = $("ed-confirm");
    if (confirmBtn.disabled) { return; }
    confirmBtn.disabled = true;
    seq += 1;
    clearTimeout(timer);
    var values = editorValues();
    send("/api/decide", values).then(function (res) {
      if (!res.ok) {
        $("ed-status").textContent = "inválido";
        showAlert("ed-alert", errorText(res.data, res.status) + (res.status === 409 ? "\nA nota já existe: troque para “Absorver”." : ""));
        if (res.data && /new_because/.test(JSON.stringify(res.data))) { $("ed-because-wrap").hidden = false; }
        confirmBtn.disabled = false;
        return;
      }
      closeModal();
      return afterDecide(values.action, res.data);
    }).catch(function () {
      if ($("ed-confirm")) { showAlert("ed-alert", "erro do servidor"); $("ed-confirm").disabled = false; }
    });
  }

  function dropValues() {
    return { id: card().dataset.id, action: "drop", reason: $("drop-reason").value };
  }

  function openDrop() {
    var c = card();
    if (modal || inflight) { return; }
    if (!c || c.dataset.empty === "true") { toast("fila vazia", "info"); return; }
    var node = $("drop-template").content.firstElementChild.cloneNode(true);
    openOverlay("drop", node);
    var title = c.querySelector("h1");
    $("drop-title").textContent = title ? title.textContent : "";
    var reason = $("drop-reason"), confirmBtn = $("drop-confirm");
    reason.addEventListener("input", function () {
      var filled = reason.value.trim().length > 0;
      $("drop-count").textContent = reason.value.length;
      confirmBtn.disabled = !filled;
      $("drop-status").textContent = filled ? "" : "informe o motivo";
      if (filled) { schedule(function () { validate(dropValues(), "drop-status", "drop-alert"); }); }
    });
    $("drop-cancel").addEventListener("click", closeModal);
    confirmBtn.addEventListener("click", submitDrop);
    $("drop-status").textContent = "informe o motivo";
    reason.focus();
  }

  function submitDrop() {
    var confirmBtn = $("drop-confirm");
    if (confirmBtn.disabled) { return; }
    confirmBtn.disabled = true;
    seq += 1;
    clearTimeout(timer);
    send("/api/decide", dropValues()).then(function (res) {
      if (!res.ok) {
        showAlert("drop-alert", errorText(res.data, res.status));
        confirmBtn.disabled = $("drop-reason").value.trim().length === 0;
        return;
      }
      closeModal();
      return afterDecide("drop", res.data);
    }).catch(function () {
      if ($("drop-alert")) { showAlert("drop-alert", "erro do servidor"); $("drop-confirm").disabled = false; }
    });
  }

  // ------------------------------------------------------------ keyboard
  function dispatch(key) {
    var action = SHORTCUTS[key];
    if (!action || modal) { return; }
    var c = card();
    if (action === "save") { decide(key, "save"); }
    else if (action === "drop") { openDrop(); }
    else if (action === "skip") { decide(key, "skip"); }
    else if (action === "absorb") {
      if (c && c.dataset.absorbTarget) { decide(key, "absorb", { note: c.dataset.absorbTarget }); }
      else { toast("sem nota similar para absorver", "error"); }
    }
    else if (action === "undo") { undo(); }
    else if (action === "next") { navigate(key, 1); }
    else if (action === "prev") { navigate(key, -1); }
    else if (action === "edit") { openEditor(); }
  }

  function typing(el) {
    if (!el || !el.tagName) { return false; }
    var tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable ||
      !!(el.closest && el.closest('[contenteditable="true"], dialog, [role="dialog"]'));
  }

  function focusables() {
    var nodes = overlay.querySelectorAll("input, textarea, select, button");
    return Array.prototype.filter.call(nodes, function (n) { return !n.disabled && !n.hidden && !n.closest("[hidden]"); });
  }

  // While a modal is open only Escape, Ctrl/Cmd+Enter and Tab act; no triage key can fire.
  function modalKey(event) {
    if (event.isComposing) { return; }
    if (event.key === "Escape") {
      event.preventDefault();
      if (modal === "editor") { cancelEditor(); } else { closeModal(); }
    } else if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      if (modal === "editor") { submitEditor(); } else { submitDrop(); }
    } else if (event.key === "Tab") {
      var items = focusables();
      if (!items.length) { return; }
      var first = items[0], last = items[items.length - 1];
      if (!overlay.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
      else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  }

  document.addEventListener("keydown", function (event) {
    if (modal) { modalKey(event); return; }
    if (event.ctrlKey || event.metaKey || event.altKey || event.repeat) { return; }
    if (typing(event.target)) { return; }
    var key = (event.key || "").toLowerCase();
    if (!SHORTCUTS[key]) { return; }
    event.preventDefault();
    dispatch(key);
  });

  var filterProject = $("filter-project");
  var filterKind = $("filter-kind");

  function onFilterChange() {
    if (filterProject) {
      if (filterProject.value) { query.project = filterProject.value; } else { delete query.project; }
    }
    if (filterKind) {
      if (filterKind.value) { query.kind = filterKind.value; } else { delete query.kind; }
    }
    app.dataset.query = JSON.stringify(query);
    var search = qs({});
    var url = window.location.pathname + (search ? "?" + search : "");
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, "", url);
    }
    load({ offset: 0 }).then(refreshStats);
  }

  if (filterProject) { filterProject.addEventListener("change", onFilterChange); }
  if (filterKind) { filterKind.addEventListener("change", onFilterChange); }

  document.querySelectorAll("button[data-key]").forEach(function (btn) {
    btn.addEventListener("click", function () { dispatch(btn.dataset.key); });
  });

  window.__review = { dispatch: dispatch, modal: function () { return modal; }, onFilterChange: onFilterChange };
})();
