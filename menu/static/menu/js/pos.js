/* Kedai Senja — keranjang kasir (tanpa dependensi). Dimuat setelah app.js. */
(() => {
  "use strict";

  const root = document.querySelector("[data-pos]");
  if (!root) return;

  const STORAGE_KEY = "kedai.cart.v1";
  const rupiah = new Intl.NumberFormat("id-ID", {
    style: "currency", currency: "IDR", maximumFractionDigits: 0,
  });
  const $ = (sel) => root.querySelector(sel);
  const $$ = (sel) => [...root.querySelectorAll(sel)];

  const tiles = $$(".tile");
  const list = $("[data-cart-list]");
  const emptyMsg = $("[data-cart-empty]");
  const form = $("[data-cart-form]");
  const cartInput = $("[data-cart-input]");
  const submitBtn = $("[data-submit]");
  const totalEl = $("[data-total]");
  const clearBtn = $("[data-clear]");
  const cashBlock = $("[data-cash-block]");
  const cashInput = $("[data-cash]");
  const changeEl = $("[data-change]");
  const bar = document.querySelector("[data-bar]");

  // Katalog dibaca dari tombol menu di halaman (id -> info produk)
  const catalog = new Map(
    tiles.map((t) => [
      Number(t.dataset.id),
      {
        id: Number(t.dataset.id),
        name: t.dataset.name,
        price: Number(t.dataset.price),
        stock: Number(t.dataset.stock),
      },
    ])
  );

  /* ---------- State keranjang: Map(id -> qty), disimpan di sessionStorage -- */
  function load() {
    const cart = new Map();
    try {
      const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "[]");
      for (const [id, qty] of saved) {
        const p = catalog.get(Number(id));
        if (p && qty > 0) cart.set(p.id, Math.min(Number(qty), p.stock)); // sesuaikan dgn stok terbaru
      }
    } catch (_) { /* data rusak: mulai kosong */ }
    return cart;
  }
  const cart = load();

  function save() {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...cart])); } catch (_) { /* abaikan */ }
  }

  const toast = (msg, type) => window.kedai?.showToast(msg, type);

  function add(id) {
    const p = catalog.get(id);
    const qty = cart.get(id) ?? 0;
    if (qty >= p.stock) {
      toast(`Stok ${p.name} hanya ${p.stock}.`, "warning");
      return;
    }
    cart.set(id, qty + 1);
    render();
  }

  function change(id, delta) {
    const p = catalog.get(id);
    const next = (cart.get(id) ?? 0) + delta;
    if (next <= 0) cart.delete(id);
    else if (next > p.stock) { toast(`Stok ${p.name} hanya ${p.stock}.`, "warning"); return; }
    else cart.set(id, next);
    render();
  }

  /* ---------- Render ------------------------------------------------------ */
  function cartLine(id, qty) {
    const p = catalog.get(id);
    const li = document.createElement("li");
    li.className = "cart__line";

    const info = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = p.name;
    const unit = document.createElement("span");
    unit.className = "muted";
    unit.textContent = rupiah.format(p.price);
    info.append(name, unit);

    const qtyBox = document.createElement("div");
    qtyBox.className = "qty";
    const mk = (label, act, text) => {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.act = act;
      b.dataset.id = id;
      b.setAttribute("aria-label", `${label} ${p.name}`);
      b.textContent = text;
      return b;
    };
    const num = document.createElement("span");
    num.textContent = qty;
    qtyBox.append(mk("Kurangi", "dec", "−"), num, mk("Tambah", "inc", "+"));

    const sub = document.createElement("strong");
    sub.className = "cart__sub";
    sub.textContent = rupiah.format(p.price * qty);

    li.append(info, qtyBox, sub);
    return li;
  }

  const paymentMethod = () => root.querySelector('input[name="payment_method"]:checked')?.value;

  function render() {
    let total = 0, count = 0;
    list.replaceChildren();
    for (const [id, qty] of cart) {
      list.append(cartLine(id, qty));
      total += catalog.get(id).price * qty;
      count += qty;
    }

    emptyMsg.hidden = cart.size > 0;
    clearBtn.hidden = cart.size === 0;
    totalEl.textContent = rupiah.format(total);
    cartInput.value = JSON.stringify([...cart].map(([id, qty]) => ({ id, qty })));

    // Lencana jumlah di tiap menu
    for (const t of tiles) {
      const id = Number(t.dataset.id);
      const qty = cart.get(id) ?? 0;
      const badge = t.querySelector(".tile__badge");
      badge.hidden = qty === 0;
      badge.textContent = `×${qty}`;
      t.classList.toggle("is-max", qty >= catalog.get(id).stock);
    }

    // Uang tunai & kembalian
    const isCash = paymentMethod() === "cash";
    cashBlock.hidden = !isCash;
    let short = false;
    changeEl.classList.remove("error");
    if (isCash && cashInput.value !== "" && total > 0) {
      const diff = Number(cashInput.value) - total;
      short = diff < 0;
      changeEl.textContent = short
        ? `Kurang ${rupiah.format(-diff)}`
        : `Kembalian ${rupiah.format(diff)}`;
      changeEl.classList.toggle("error", short);
    } else {
      changeEl.textContent = "\u00A0";
    }

    submitBtn.disabled = cart.size === 0 || short;

    // Bilah ringkas untuk layar HP
    if (bar) {
      bar.hidden = cart.size === 0;
      bar.querySelector("[data-bar-count]").textContent = `${count} item`;
      bar.querySelector("[data-bar-total]").textContent = rupiah.format(total);
    }
    save();
  }

  /* ---------- Event ------------------------------------------------------- */
  root.addEventListener("click", (e) => {
    const tile = e.target.closest(".tile");
    if (tile) { add(Number(tile.dataset.id)); return; }

    const btn = e.target.closest("[data-act]");
    if (btn) { change(Number(btn.dataset.id), btn.dataset.act === "inc" ? 1 : -1); return; }

    if (e.target.closest("[data-clear]")) { cart.clear(); render(); return; }

    if (e.target.closest("[data-exact]")) {
      let total = 0;
      for (const [id, qty] of cart) total += catalog.get(id).price * qty;
      cashInput.value = total || "";
      render();
    }
  });

  root.addEventListener("input", (e) => {
    if (e.target === cashInput) render();
  });
  root.addEventListener("change", (e) => {
    if (e.target.name === "payment_method") render();
  });

  form.addEventListener("submit", (e) => {
    if (cart.size === 0) { e.preventDefault(); return; }
    submitBtn.disabled = true; // cegah klik ganda
    submitBtn.textContent = "Menyimpan…";
  });

  /* ---------- Pencarian & filter kategori --------------------------------- */
  const search = $("[data-search]");
  const chips = $$(".chip-btn");
  const noResults = $("[data-no-results]");
  let activeCat = "all";

  function applyFilter() {
    const q = (search?.value ?? "").trim().toLowerCase();
    let shown = 0;
    for (const t of tiles) {
      const ok =
        (activeCat === "all" || t.dataset.category === activeCat) &&
        t.dataset.name.toLowerCase().includes(q);
      t.hidden = !ok;
      if (ok) shown++;
    }
    if (noResults) noResults.hidden = shown > 0;
  }

  search?.addEventListener("input", applyFilter);
  chips.forEach((chip) =>
    chip.addEventListener("click", () => {
      activeCat = chip.dataset.filter;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      applyFilter();
    })
  );

  render();
})();
