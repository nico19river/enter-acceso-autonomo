
// MENU DESPLEGABLE

document.addEventListener('DOMContentLoaded', () => {
  const userButton = document.getElementById('user-button');
  const dropdown = document.getElementById('dropdown');

  userButton.addEventListener('click', (e) => {
    e.stopPropagation(); // Evita que el click cierre el menú inmediatamente
    userButton.classList.toggle('active');
    dropdown.classList.toggle('show');
  });

      // Cerrar el dropdown si se hace click afuera
  document.addEventListener('click', () => {
    dropdown.classList.remove('show');
    userButton.classList.remove('active');
  });

// NAV LATERAL

const links = document.querySelectorAll('[data-section]'); //almacena todos los elementos que tengan data-section en el HTML
const main = document.querySelector('.main-dinamico'); //almacena el main-dinamico donde se van a cargar las secciones

 links.forEach(link => {
    link.addEventListener('click', (e) => {  //agrega un evento e con la info de cada evento
      e.preventDefault(); // Evita que el enlace recargue la página

      const section = link.getAttribute('data-section'); // Lee el valor de data-section

      // Petición GET a la ruta correspondiente
      fetch(`/${section}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`No se pudo cargar la sección: ${section}`);
          }
          return response.text(); // Convertimos la respuesta en texto HTML para que flask lo renderice
        })
        .then(html => {
          //cargamos el contenido HTML en el main dinamico
          main.innerHTML = html;

        })
        .catch(error => {
          console.error(error); // Si hay error, lo muestra por consola
          main.innerHTML = '<p>Error al cargar la sección.</p>';
        });
    });
  });
});



