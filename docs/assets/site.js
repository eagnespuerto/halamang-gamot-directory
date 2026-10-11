// Search, colour filter and sorting for the plant grid on the home page.
(function () {
  var grid = document.getElementById('grid');
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.children);
  var input = document.getElementById('q');
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var sort = document.getElementById('sort');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var color = '';

  function fold(s) {
    return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  }

  function apply() {
    var words = fold(input.value).split(/\s+/).filter(Boolean);
    var shown = 0;
    cards.forEach(function (card) {
      var q = card.dataset.q;
      var ok = words.every(function (w) { return q.indexOf(w) !== -1; });
      if (ok && color) ok = card.dataset.colors.split(' ').indexOf(color) !== -1;
      card.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? ' entry' : ' entries');
    empty.hidden = shown !== 0;
  }

  input.addEventListener('input', apply);

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      color = color === chip.dataset.color ? '' : chip.dataset.color;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.color === color)); });
      apply();
    });
  });

  sort.addEventListener('change', function () {
    var key = sort.value;
    cards.sort(function (a, b) {
      if (key === 'n') return a.dataset.n - b.dataset.n;
      return a.dataset[key].localeCompare(b.dataset[key]);
    });
    cards.forEach(function (card) { grid.appendChild(card); });
  });

  // A ?q= in the address pre-fills the search.
  var initial = new URLSearchParams(location.search).get('q');
  if (initial) { input.value = initial; }
  apply();
})();
