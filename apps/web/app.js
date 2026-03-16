const currency = new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 });

const branches = [
  {
    id: "br_01",
    name: "Sucursal Centro",
    address: "Av. Libertador Bernardo O'Higgins 949, Santiago",
    bingEmbedUrl: "https://www.bing.com/maps/embed?h=280&w=1024&cp=-33.4429~-70.6506&lvl=16&typ=d&sty=r&src=SHELL&FORM=MBEDV8",
  },
  {
    id: "br_02",
    name: "Sucursal Norte",
    address: "Av. Independencia 565, Independencia, Santiago",
    bingEmbedUrl: "https://www.bing.com/maps/embed?h=280&w=1024&cp=-33.4196~-70.6518&lvl=16&typ=d&sty=r&src=SHELL&FORM=MBEDV8",
  },
];

const catalogByBranch = {
  br_01: [
    { id: "prod_001", name: "Arroz 1kg", price: 1290, stock: 18 },
    { id: "prod_002", name: "Aceite 1L", price: 2390, stock: 8 },
    { id: "prod_003", name: "Leche Entera", price: 1090, stock: 0 },
  ],
  br_02: [
    { id: "prod_001", name: "Arroz 1kg", price: 1290, stock: 5 },
    { id: "prod_004", name: "Fideos 400g", price: 890, stock: 15 },
    { id: "prod_005", name: "Azúcar 1kg", price: 1290, stock: 12 },
  ],
};

const pickupSlotsByBranch = {
  br_01: ["10:00 - 11:00", "11:00 - 12:00", "17:00 - 18:00"],
  br_02: ["09:00 - 10:00", "12:00 - 13:00", "18:00 - 19:00"],
};

let selectedBranch = branches[0].id;
let cart = [];

const branchSelect = document.querySelector("#branch");
const catalog = document.querySelector("#catalog");
const cartItems = document.querySelector("#cart-items");
const subtotal = document.querySelector("#subtotal");
const checkoutForm = document.querySelector("#checkout-form");
const pickupSlotSelect = document.querySelector("#pickup-slot");
const checkoutStatus = document.querySelector("#checkout-status");
const mapFrame = document.querySelector("#bing-map-frame");
const storeAddress = document.querySelector("#store-address");

function renderBranches() {
  branches.forEach((branch) => {
    const option = document.createElement("option");
    option.value = branch.id;
    option.textContent = branch.name;
    branchSelect.append(option);
  });
}

function renderCatalog() {
  catalog.innerHTML = "";
  catalogByBranch[selectedBranch].forEach((product) => {
    const card = document.createElement("article");
    card.className = "product-card";
    card.innerHTML = `
      <strong>${product.name}</strong>
      <span>${currency.format(product.price)}</span>
      <small>Stock sucursal: ${product.stock}</small>
      <button ${product.stock <= 0 ? "disabled" : ""} data-id="${product.id}">Agregar</button>
    `;
    card.querySelector("button")?.addEventListener("click", () => addToCart(product));
    catalog.append(card);
  });
}


function renderPublicStoreMap() {
  const branch = branches.find((item) => item.id === selectedBranch);
  if (!branch) return;
  mapFrame.src = branch.bingEmbedUrl;
  storeAddress.textContent = `${branch.name} · ${branch.address}`;
}

function renderPickupSlots() {
  pickupSlotSelect.innerHTML = "";
  pickupSlotsByBranch[selectedBranch].forEach((slot, idx) => {
    const option = document.createElement("option");
    option.value = slot;
    option.textContent = slot;
    if (idx === 0) option.selected = true;
    pickupSlotSelect.append(option);
  });
}

function addToCart(product) {
  const existing = cart.find((item) => item.id === product.id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }
  renderCart();
}

function renderCart() {
  cartItems.innerHTML = "";
  if (cart.length === 0) {
    cartItems.innerHTML = "<li>Sin productos.</li>";
  } else {
    cart.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.name} x${item.qty}`;
      cartItems.append(li);
    });
  }
  const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  subtotal.textContent = currency.format(total);
}

branchSelect.addEventListener("change", (event) => {
  selectedBranch = event.target.value;
  cart = [];
  checkoutStatus.textContent = "";
  checkoutStatus.className = "status";
  renderCatalog();
  renderPickupSlots();
  renderPublicStoreMap();
  renderCart();
});

checkoutForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (cart.length === 0) {
    checkoutStatus.textContent = "Agrega al menos un producto antes de confirmar.";
    checkoutStatus.className = "status error";
    return;
  }

  const data = new FormData(checkoutForm);
  const orderId = `ord_${Math.floor(Math.random() * 99999)}`;
  checkoutStatus.textContent = `Pedido ${orderId} creado en estado recibido (${branchSelect.selectedOptions[0].text} · Slot ${data.get("pickup-slot") || pickupSlotSelect.value}).`;
  checkoutStatus.className = "status ok";

  checkoutForm.reset();
  renderPickupSlots();
  cart = [];
  renderCart();
});

renderBranches();
renderCatalog();
renderPickupSlots();
renderPublicStoreMap();
renderCart();
