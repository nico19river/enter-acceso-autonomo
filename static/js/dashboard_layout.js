document.addEventListener('DOMContentLoaded', () => {
  const userButton = document.getElementById('user-button');
  const dropdown = document.getElementById('dropdown');
  const links = document.querySelectorAll('[data-section]');
  const main = document.querySelector('.main-dinamico');

  // MENÚ USUARIO
  userButton.addEventListener('click', (e) => {
    e.stopPropagation();
    userButton.classList.toggle('active');
    dropdown.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    dropdown.classList.remove('show');
    userButton.classList.remove('active');
  });

  // FUNCIONALIDAD PARA ENLACES DE NAVEGACIÓN
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const section = link.getAttribute('data-section');
      cargarSeccion(section);
    });
  });

  // DELEGACIÓN DE EVENTOS EN MAIN PARA ENLACES DINÁMICOS
  main.addEventListener('click', (e) => {
    const target = e.target.closest('[data-section]');
    if (target) {
      e.preventDefault();
      const section = target.getAttribute('data-section');
      cargarSeccion(section);
    }
  });

  // FUNCIÓN PRINCIPAL PARA CARGAR SECCIONES
  function cargarSeccion(section) {
  fetch(`/${section}`)
    .then(response => {
      if (!response.ok) throw new Error(`No se pudo cargar la sección: ${section}`);
      return response.text();
    })
    .then(html => {
      main.innerHTML = html;

      // Ejecutar scripts inline o externos que estén en el HTML cargado dinámicamente
      const scripts = main.querySelectorAll('script');
      scripts.forEach(oldScript => {
        const newScript = document.createElement('script');
        if (oldScript.src) {
          newScript.src = oldScript.src;
        } else {
          newScript.textContent = oldScript.textContent;
        }
        document.body.appendChild(newScript);
        document.body.removeChild(newScript);
      });

      if (section === 'borrar-usuario') {
        prepararFormularioBorrarUsuario(); // Inicializá el formulario si es esa sección
      }
    })
    .catch(error => {
      console.error(error);
      main.innerHTML = '<p>Error al cargar la sección.</p>';
    });
}

  // PREPARAR EL FORMULARIO DE BORRAR USUARIO
  function prepararFormularioBorrarUsuario() {
    const form = document.getElementById('form-borrar-usuario');
    if (form) {
      console.log("✅ Formulario de borrar-usuario detectado. Agregando listener...");
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        console.log("🔍 Submit detectado en borrar-usuario");
        const termino = document.getElementById('termino_busqueda').value;

        fetch('/borrar-usuario', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: new URLSearchParams({ 'termino_busqueda': termino })
        })
        .then(response => response.text())
        .then(html => {
          const contenedorResultados = document.getElementById('resultado-usuarios');
          if (contenedorResultados) {
            contenedorResultados.innerHTML = html;
          }
        })
        .catch(error => console.error(error));
      });
    }
  }
});
