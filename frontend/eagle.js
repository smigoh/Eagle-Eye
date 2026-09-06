document.addEventListener('DOMContentLoaded', () => {
  const panels = Array.from(document.querySelectorAll('.glass-panel'));
  const links = Array.from(document.querySelectorAll('.panel-link'));
  let current = 0;

  function showPanel(index) {
    if (index === current) return;
    panels[current].classList.remove('active');
    panels[current].classList.add('slide-out');
    panels[index].style.display = 'block';
    panels[index].classList.remove('slide-out');
    setTimeout(() => {
      panels[current].style.display = 'none';
      panels[current].classList.remove('slide-out');
      panels[index].classList.add('active');
      current = index;
    }, 400);
  }

  links.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const index = Number(link.dataset.target);
      showPanel(index);
    });
  });

  // County dropdown
  const countyBtn = document.getElementById('county-btn');
  const countyDropdown = document.getElementById('county-dropdown');
  const govNameEls = Array.from(document.querySelectorAll('.gov-name'));
  const counties = ["Baringo","Bomet","Bungoma","Busia","Elgeyo Marakwet","Embu","Garissa","Homa Bay",
    "Isiolo","Kajiado","Kakamega","Kericho","Kiambu","Kilifi","Kirinyaga","Kisii","Kisumu",
    "Kitui","Kwale","Laikipia","Lamu","Machakos","Makueni","Mandera","Marsabit","Meru","Migori",
    "Mombasa","Murang'a","Nairobi","Narok","Nyamira","Nyandarua","Nyeri","Samburu","Siaya","Taita Taveta",
    "Tana River","Tharaka Nithi","Trans Nzoia","Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot"];

  counties.forEach(c => {
    const li = document.createElement('li');
    li.textContent = c;
    li.addEventListener('click', () => {
      countyBtn.textContent = c.toUpperCase();
      govNameEls.forEach(h => h.textContent = `${c.toUpperCase()} COUNTY GOVERNMENT`);
      localStorage.setItem('selectedCounty', c.toUpperCase());
      countyDropdown.style.display = 'none';
    });
    countyDropdown.appendChild(li);
  });

  // Load saved county
  const savedCounty = localStorage.getItem('selectedCounty');
  if (savedCounty) {
    countyBtn.textContent = savedCounty;
    govNameEls.forEach(h => h.textContent = `${savedCounty} COUNTY GOVERNMENT`);
  }

  countyBtn.addEventListener('click', () => {
    countyDropdown.style.display = countyDropdown.style.display === 'block' ? 'none' : 'block';
  });

  document.addEventListener('click', e => {
    if (!countyBtn.contains(e.target) && !countyDropdown.contains(e.target)) {
      countyDropdown.style.display = 'none';
    }
  });

  // Signup / login
  document.querySelectorAll('.signup, .login-btn').forEach(el => {
    el.addEventListener('click', () => { window.location.href='login.html'; });
  });
});
