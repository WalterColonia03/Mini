(() => {
  const capture = document.getElementById('barcode-capture');
  const dialog = document.getElementById('barcode-capture-dialog');
  if (!capture || typeof dialog?.showModal !== 'function') return;

  const destination = document.getElementById(capture.dataset.destination);
  const open = document.getElementById('barcode-capture-open');
  const input = document.getElementById('barcode-capture-input');
  const apply = document.getElementById('barcode-capture-apply');
  const cancel = document.getElementById('barcode-capture-cancel');
  const error = document.getElementById('barcode-capture-error');
  if (!destination?.form) return;

  const type = destination.form.elements.namedItem('barcode_type');
  const status = document.getElementById('barcode-capture-status');
  const destinationStatus = document.createElement('p');
  destinationStatus.id = destination.id + '_barcode_check';
  destinationStatus.className = 'help';
  destinationStatus.setAttribute('role', 'status');
  destinationStatus.setAttribute('aria-live', 'polite');
  destinationStatus.setAttribute('aria-atomic', 'true');
  destination.after(destinationStatus);
  destination.setAttribute('aria-describedby',
    [destination.getAttribute('aria-describedby'), destinationStatus.id].filter(Boolean).join(' '));

  // A result describes only the exact value requested. A newer scan invalidates it.
  function watchCode(field, message, available) {
    let version = 0, timer, controller, lastValue = null;
    function reset() {
      version += 1;
      lastValue = null;
      clearTimeout(timer);
      controller?.abort();
      message.textContent = '';
      available?.(false);
    }
    async function check(token, value, kind) {
      controller = new AbortController();
      const requestController = controller;
      const timeout = setTimeout(() => requestController.abort(), 5000);
      let receivedResponse = false;
      try {
        const url = new URL(capture.dataset.checkUrl, window.location.origin);
        url.searchParams.set('barcode', value);
        if (type) url.searchParams.set('barcode_type', kind);
        if (capture.dataset.productId) url.searchParams.set('product_id', capture.dataset.productId);
        const response = await fetch(url, {signal: controller.signal, cache: 'no-store', headers: {Accept: 'application/json'}});
        receivedResponse = true;
        const data = await response.json();
        if (token !== version || field.value !== value || (type?.value || '') !== kind) return;
        if (response.status === 400 && data.error) {
          message.textContent = data.error;
          available?.(false);
        } else if (!response.ok || typeof data.duplicate !== 'boolean') {
          throw new Error('Unavailable');
        } else {
          message.textContent = data.duplicate ? 'El código de barras ya está registrado' :
            'Sin duplicados en esta consulta. Se volverá a comprobar al guardar.';
          available?.(!data.duplicate);
        }
      } catch (_) {
        if (token !== version || field.value !== value || (type?.value || '') !== kind) return;
        message.textContent = receivedResponse ? 'No se pudo validar la respuesta. Vuelva a consultar el código.' : 'No se pudo comprobar el código. Se validará al guardar.';
        available?.(!receivedResponse);
      } finally {
        clearTimeout(timeout);
      }
    }
    function schedule(immediate = false) {
      const key = JSON.stringify([field.value, type?.value || '']);
      if (lastValue === key) return;
      reset();
      lastValue = key;
      if (!field.value.trim()) return;
      if (type && !type.value) { message.textContent = 'Seleccione el tipo de código antes de comprobarlo.'; return; }
      const token = version, value = field.value, kind = type?.value || '';
      message.textContent = 'Comprobando código…';
      timer = setTimeout(() => check(token, value, kind), immediate ? 0 : 250);
    }
    field.addEventListener('input', () => schedule());
    field.addEventListener('change', () => schedule(true));
    type?.addEventListener('change', () => schedule(true));
    return {reset};
  }
  const scanCheck = watchCode(input, status, ready => { apply.disabled = !ready; });
  watchCode(destination, destinationStatus);

  let replaceOnInsert = false;
  open.addEventListener('click', () => {
    replaceOnInsert = false;
    scanCheck.reset();
    input.value = '';
    error.textContent = '';
    apply.disabled = true;
    dialog.showModal();
    input.focus();
  });

  dialog.addEventListener('keydown', event => {
    if (event.ctrlKey && event.key.toLowerCase() === 'a') {
      // Barcode to PC's replace command can arrive while a dialog button has focus.
      event.preventDefault();
      input.focus();
      input.select();
      replaceOnInsert = true;
    } else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'Tab', 'Escape'].includes(event.key)) {
      replaceOnInsert = false;
    } else if (event.target === input && event.key === 'Enter') {
      event.preventDefault();
    }
  });

  // A text field with maxlength silently truncates oversized scans and pastes.
  // Do not offer the truncated prefix as a code.
  function checkLength(event, inserted) {
    if (!inserted) return;
    const retained = input.value.length - (input.selectionEnd - input.selectionStart);
    if (retained + inserted.length > input.maxLength) {
      event.preventDefault();
      scanCheck.reset();
      apply.disabled = true;
      error.textContent = 'El código supera los ' + input.maxLength + ' caracteres. Vuelva a leerlo o corrija el valor.';
    }
  }
  // With keyboard-emulated scans the selection can collapse before the first
  // character arrives. Honour the replace command at insertion time as well.
  input.addEventListener('pointerdown', () => { replaceOnInsert = false; });
  input.addEventListener('beforeinput', event => {
    if (replaceOnInsert && event.inputType.startsWith('insert')) input.select();
    replaceOnInsert = false;
    checkLength(event, event.data);
  });
  input.addEventListener('paste', event => {
    if (replaceOnInsert) input.select();
    checkLength(event, event.clipboardData?.getData('text/plain'));
  });
  input.addEventListener('input', () => {
    error.textContent = '';
    // Availability is set only by the check for the current complete value.
  });

  apply.addEventListener('click', () => {
    if (apply.disabled) return;
    destination.value = input.value;
    destination.dispatchEvent(new Event('input', {bubbles: true}));
    destination.dispatchEvent(new Event('change', {bubbles: true}));
    dialog.close();
  });
  cancel.addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { scanCheck.reset(); open.focus(); });
  destination.form.addEventListener('submit', event => {
    if (dialog.open) event.preventDefault();
  });
  capture.hidden = false;
})();
