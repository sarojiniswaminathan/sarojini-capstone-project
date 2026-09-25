(function () {
  const tree = document.getElementById('fabric-tree');
  const categoryTemplate = document.getElementById('tree-category-template');
  const materialTemplate = document.getElementById('tree-material-template');
  const addTemplate = document.getElementById('tree-add-template');

  const openCategories = new Set();

  function titleCase(word) {
    return (word || 'Other').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function groupByCategory(materials) {
    const groups = new Map();
    materials.forEach((material) => {
      const key = material.category || 'other';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(material);
    });
    return groups;
  }

  function renderMaterial(material) {
    const node = materialTemplate.content.cloneNode(true);
    const leaf = node.querySelector('.tree-leaf');
    const label = node.querySelector('.tree-leaf-label');
    const detail = node.querySelector('.tree-material-detail');
    const swatch = node.querySelector('.tree-leaf-swatch');
    const img = swatch.querySelector('img');

    const hasSwatch = Boolean(material.photo_url || material.color);
    if (hasSwatch) {
      swatch.hidden = false;
      if (material.photo_url) {
        img.src = material.photo_url;
        img.hidden = false;
      } else {
        swatch.style.background = material.color.toLowerCase();
      }
    }

    label.textContent = material.color ? `${material.name} — ${material.color}` : material.name;
    label.setAttribute('aria-selected', 'false');
    node.querySelector('.tree-material-qty').textContent =
      `${material.available_qty} ${material.unit} available · ${material.physical_qty} total · ${material.reserved_qty} reserved`;

    function toggleSelected() {
      const isSelected = leaf.classList.toggle('selected');
      label.setAttribute('aria-selected', String(isSelected));
      detail.hidden = !isSelected;
    }

    label.addEventListener('click', toggleSelected);

    const fileInput = node.querySelector('.photo-upload input');
    fileInput.addEventListener('change', async (event) => {
      event.stopPropagation();
      if (!fileInput.files.length) return;
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      await fetch(`/inventory/${encodeURIComponent(material.id)}/photo`, {
        method: 'POST',
        body: formData,
      });
      loadInventory();
    });
    node.querySelector('.photo-upload').addEventListener('click', (event) => event.stopPropagation());

    const qtyInput = node.querySelector('.material-adjust input');
    const saveBtn = node.querySelector('.material-adjust button');
    saveBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      const delta = parseFloat(qtyInput.value);
      if (Number.isNaN(delta) || delta === 0) return;
      await fetch(`/inventory/${encodeURIComponent(material.id)}/adjust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta, note: 'Adjusted from the fabric tree' }),
      });
      qtyInput.value = '';
      loadInventory();
      if (window.refreshCalendar) window.refreshCalendar();
    });

    return node;
  }

  function renderAddRow(categoryKey) {
    const node = addTemplate.content.cloneNode(true);
    const toggleBtn = node.querySelector('.tree-add-toggle');
    const form = node.querySelector('.tree-add-form');
    const nameInput = form.querySelector('.tree-add-name');
    const colorInput = form.querySelector('.tree-add-color');
    const qtyInput = form.querySelector('.tree-add-qty');
    const unitInput = form.querySelector('.tree-add-unit');
    const photoInput = form.querySelector('.tree-add-photo');
    const photoNameLabel = form.querySelector('.tree-add-photo-name');

    toggleBtn.addEventListener('click', () => {
      form.hidden = !form.hidden;
    });

    photoInput.addEventListener('change', () => {
      photoNameLabel.textContent = photoInput.files.length ? photoInput.files[0].name : '';
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const name = nameInput.value.trim();
      const unit = unitInput.value.trim();
      if (!name || !unit) return;

      const res = await fetch('/inventory/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          category: categoryKey,
          unit,
          physical_qty: parseFloat(qtyInput.value) || 0,
          color: colorInput.value.trim() || null,
        }),
      });
      const created = await res.json();

      if (photoInput.files.length) {
        const formData = new FormData();
        formData.append('file', photoInput.files[0]);
        await fetch(`/inventory/${encodeURIComponent(created.material_id)}/photo`, {
          method: 'POST',
          body: formData,
        });
      }

      openCategories.add(categoryKey);
      loadInventory();
    });

    return node;
  }

  function renderCategory(name, materials) {
    const node = categoryTemplate.content.cloneNode(true);
    const header = node.querySelector('.tree-category-header');
    const chevron = node.querySelector('.tree-chevron');
    const children = node.querySelector('.tree-children');

    node.querySelector('.tree-category-name').textContent = titleCase(name);
    const isOpen = openCategories.has(name);
    header.setAttribute('aria-expanded', String(isOpen));
    if (isOpen) {
      children.classList.add('open');
      chevron.classList.add('open');
    }

    materials.forEach((material) => children.appendChild(renderMaterial(material)));
    children.appendChild(renderAddRow(name));

    header.addEventListener('click', () => {
      const nowOpen = children.classList.toggle('open');
      chevron.classList.toggle('open', nowOpen);
      header.setAttribute('aria-expanded', String(nowOpen));
      if (nowOpen) {
        openCategories.add(name);
      } else {
        openCategories.delete(name);
      }
    });

    return node;
  }

  async function loadInventory() {
    try {
      const res = await fetch('/inventory/glance');
      const data = await res.json();
      tree.innerHTML = '';
      const groups = groupByCategory(data.materials || []);
      groups.forEach((materials, category) => {
        tree.appendChild(renderCategory(category, materials));
      });
    } catch (err) {
      console.error(err);
    }
  }

  loadInventory();
  window.refreshInventory = loadInventory;
})();
