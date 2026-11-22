/* Kedai Senja — interaksi frontend (tanpa dependensi) */
(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ?? "";
  const toastBox = document.getElementById("toasts");

  /* ---------- Toast ------------------------------------------------------ */
  function armToast(el) {
    const close = () => {
      el.classList.add("is-leaving");
      setTimeout(() => el.remove(), 220);
    };
    el.querySelector("button")?.addEventListener("click", close);
    setTimeout(close, 4500);
  }

  function showToast(text, type = "success") {
    const el = document.createElement("div");
    el.className = `toast toast--${type}`;
    const span = document.createElement("span");
    span.textContent = text; // textContent: aman dari injeksi HTML
    const btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("aria-label", "Tutup pesan");
    btn.innerHTML = "&times;";
    el.append(span, btn);
    toastBox.append(el);
    armToast(el);
  }

  toastBox?.querySelectorAll(".toast").forEach(armToast);

  /* ---------- Dialog konfirmasi hapus ------------------------------------ */
  const dialog = document.getElementById("confirm-dialog");
  const confirmForm = document.getElementById("confirm-form");
  const dialogTitle = document.getElementById("dialog-title");
  const dialogText = document.getElementById("dialog-text");
  const dialogConfirm = document.getElementById("dialog-confirm");
  const dialogDismiss = document.getElementById("dialog-dismiss");

  dialog?.addEventListener("click", (e) => {
    if (e.target === dialog) dialog.close(); // klik area gelap = batal
  });

  /* ---------- Switch status dijual (AJAX) -------------------------------- */
  async function toggleAvailability(sw) {
    sw.disabled = true;
    try {
      const res = await fetch(sw.dataset.toggleUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken, Accept: "application/json" },
        credentials: "same-origin",
      });
      if (res.status === 401) {
        showToast("Sesi berakhir. Muat ulang halaman lalu masuk lagi.", "error");
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      sw.setAttribute("aria-checked", String(data.is_available));
      const label = sw.parentElement.querySelector(".switch-label");
      if (label) label.textContent = data.is_available ? "Dijual" : "Habis";

      const avail = document.getElementById("stat-available");
      const unavail = document.getElementById("stat-unavailable");
      if (avail) avail.textContent = data.available_count;
      if (unavail) unavail.textContent = data.unavailable_count;

      showToast(`${data.name} ${data.is_available ? "dijual kembali" : "ditandai habis"}.`);
    } catch (err) {
      showToast("Status belum berubah. Periksa koneksi lalu coba lagi.", "error");
    } finally {
      sw.disabled = false;
    }
  }

  /* ---------- Delegasi klik --------------------------------------------- */
  document.addEventListener("click", (e) => {
    const del = e.target.closest("[data-delete-url]");
    if (del && dialog) {
      const d = del.dataset;
      confirmForm.action = d.deleteUrl;
      dialogTitle.textContent = d.confirmTitle || `Hapus “${d.deleteName}”?`;
      dialogText.textContent = d.confirmText || "Data yang sudah dihapus tidak bisa dikembalikan.";
      dialogConfirm.textContent = d.confirmLabel || "Hapus";
      dialogDismiss.textContent = d.dismissLabel || "Batal";
      dialog.showModal();
      return;
    }
    if (e.target.closest("[data-close]")) {
      dialog?.close();
      return;
    }
    const sw = e.target.closest(".switch");
    if (sw && !sw.disabled) toggleAvailability(sw);
  });

  /* ---------- Filter: kirim otomatis saat dropdown berubah --------------- */
  document.querySelectorAll("form[data-autosubmit]").forEach((form) => {
    form.querySelectorAll("select").forEach((s) =>
      s.addEventListener("change", () => form.requestSubmit())
    );
  });

  /* ---------- Form menu: pratinjau foto & harga -------------------------- */
  const fileInput = document.querySelector("[data-image-input]");
  const previewBox = document.querySelector("[data-image-preview]");
  fileInput?.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file || !file.type.startsWith("image/")) return;
    const img = new Image();
    img.alt = "Pratinjau foto menu";
    img.src = URL.createObjectURL(file);
    img.onload = () => URL.revokeObjectURL(img.src);
    previewBox.replaceChildren(img);
  });

  const priceInput = document.querySelector("[data-price-input]");
  const pricePreview = document.querySelector("[data-price-preview]");
  if (priceInput && pricePreview) {
    const rupiah = new Intl.NumberFormat("id-ID", {
      style: "currency", currency: "IDR", maximumFractionDigits: 0,
    });
    const render = () => {
      const n = Number(priceInput.value);
      pricePreview.textContent = n > 0 ? `Tampil di menu: ${rupiah.format(n)}` : "\u00A0";
    };
    priceInput.addEventListener("input", render);
    render();
  }

  /* ---------- Cetak struk & pilih tanggal -------------------------------- */
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-print]")) window.print();
  });
  document.querySelectorAll("form[data-autosubmit-date]").forEach((form) => {
    form.querySelector("input[type=date]")?.addEventListener("change", () => form.requestSubmit());
  });

  /* ---------- Dipakai bersama oleh halaman kasir ------------------------- */
  window.kedai = { showToast };

  // Setelah pesanan tersimpan, kosongkan keranjang kasir yang tersimpan di browser
  if (document.querySelector("[data-clear-cart]")) {
    try { sessionStorage.removeItem("kedai.cart.v1"); } catch (_) { /* abaikan */ }
  }
})();
