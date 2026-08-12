/* =========================================================
   FINDPETS
   JAVASCRIPT GENERAL
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    iniciarMenuMovil();

    iniciarBotonesContrasena();

    iniciarVistaPreviaImagenes();

    iniciarConfirmaciones();

    iniciarChat();

    iniciarUbicacion();

});


/* =========================================================
   MENÚ MÓVIL
========================================================= */

function iniciarMenuMovil() {

    const botonMenu = document.getElementById("botonMenu");

    const menu = document.getElementById("menuPrincipal");


    if (!botonMenu || !menu) {

        return;

    }


    botonMenu.addEventListener("click", function () {

        menu.classList.toggle("activo");


        const estaAbierto = menu.classList.contains("activo");


        botonMenu.setAttribute(
            "aria-expanded",
            estaAbierto
        );


        const icono = botonMenu.querySelector(
            ".material-icons-rounded"
        );


        if (icono) {

            if (estaAbierto) {

                icono.textContent = "close";

            } else {

                icono.textContent = "menu";

            }

        }

    });


    const enlaces = menu.querySelectorAll("a");


    enlaces.forEach(function (enlace) {

        enlace.addEventListener("click", function () {

            menu.classList.remove("activo");

            botonMenu.setAttribute(
                "aria-expanded",
                "false"
            );


            const icono = botonMenu.querySelector(
                ".material-icons-rounded"
            );


            if (icono) {

                icono.textContent = "menu";

            }

        });

    });

}


/* =========================================================
   MOSTRAR / OCULTAR CONTRASEÑA
========================================================= */

function iniciarBotonesContrasena() {

    const botones = document.querySelectorAll(
        ".boton-ver-contrasena"
    );


    botones.forEach(function (boton) {

        boton.addEventListener("click", function () {

            let input = null;


            const idInput = boton.getAttribute("data-input");


            if (idInput) {

                input = document.getElementById(idInput);

            }


            if (!input) {

                const contenedor = boton.closest(
                    ".campo-con-boton"
                );


                if (contenedor) {

                    input = contenedor.querySelector(
                        "input[type='password'], input[type='text']"
                    );

                }

            }


            if (!input) {

                return;

            }


            const icono = boton.querySelector(
                ".material-icons-rounded"
            );


            if (input.type === "password") {

                input.type = "text";


                if (icono) {

                    icono.textContent = "visibility_off";

                }


                boton.setAttribute(
                    "aria-label",
                    "Ocultar contraseña"
                );

            } else {

                input.type = "password";


                if (icono) {

                    icono.textContent = "visibility";

                }


                boton.setAttribute(
                    "aria-label",
                    "Mostrar contraseña"
                );

            }

        });

    });

}


/* =========================================================
   PREVISUALIZAR IMÁGENES
========================================================= */

function iniciarVistaPreviaImagenes() {

    const inputsImagen = document.querySelectorAll(
        "input[type='file'][accept*='image']"
    );


    inputsImagen.forEach(function (input) {

        input.addEventListener("change", function () {

            const archivo = input.files[0];


            if (!archivo) {

                return;

            }


            if (!archivo.type.startsWith("image/")) {

                alert(
                    "Selecciona un archivo de imagen válido."
                );

                input.value = "";

                return;

            }


            mostrarNombreArchivo(
                input,
                archivo.name
            );


            actualizarFotoPerfil(
                input,
                archivo
            );

        });

    });

}


/* =========================================================
   MOSTRAR NOMBRE DEL ARCHIVO
========================================================= */

function mostrarNombreArchivo(input, nombreArchivo) {

    let texto = input.parentElement.querySelector(
        ".nombre-archivo"
    );


    if (!texto) {

        texto = document.createElement("small");

        texto.className = "nombre-archivo";

        input.parentElement.appendChild(texto);

    }


    texto.textContent = "Imagen seleccionada: " + nombreArchivo;

}


/* =========================================================
   PREVISUALIZAR FOTO DE PERFIL
========================================================= */

function actualizarFotoPerfil(input, archivo) {

    if (input.id !== "foto_perfil") {

        return;

    }


    const lector = new FileReader();


    lector.addEventListener("load", function () {

        const contenedor = document.querySelector(
            ".foto-perfil-edicion"
        );


        if (!contenedor) {

            return;

        }


        let imagen = contenedor.querySelector("img");


        if (!imagen) {

            imagen = document.createElement("img");

            contenedor.innerHTML = "";

            contenedor.appendChild(imagen);

        }


        imagen.src = lector.result;

        imagen.alt = "Vista previa de la foto de perfil";

    });


    lector.readAsDataURL(archivo);

}


/* =========================================================
   CONFIRMACIONES
========================================================= */

function iniciarConfirmaciones() {

    const botonesEliminar = document.querySelectorAll(
        ".boton-eliminar, .boton-peligro"
    );


    botonesEliminar.forEach(function (boton) {

        if (boton.hasAttribute("onclick")) {

            return;

        }


        boton.addEventListener("click", function (evento) {

            const formulario = boton.closest("form");


            if (!formulario) {

                return;

            }


            const confirmar = window.confirm(
                "¿Estás seguro de que deseas realizar esta acción?"
            );


            if (!confirmar) {

                evento.preventDefault();

            }

        });

    });

}


/* =========================================================
   CHAT
========================================================= */

function iniciarChat() {

    const mensajes = document.querySelector(
        ".mensajes-chat"
    );


    if (!mensajes) {

        return;

    }


    mensajes.scrollTop = mensajes.scrollHeight;


    const formulario = document.querySelector(
        ".formulario-chat"
    );


    if (!formulario) {

        return;

    }


    const inputMensaje = formulario.querySelector(
        "input[name='mensaje']"
    );


    if (!inputMensaje) {

        return;

    }


    inputMensaje.addEventListener(
        "keydown",
        function (evento) {

            if (
                evento.key === "Enter" &&
                !evento.shiftKey
            ) {

                evento.preventDefault();


                if (inputMensaje.value.trim() !== "") {

                    formulario.submit();

                }

            }

        }
    );

}


/* =========================================================
   UBICACIÓN
========================================================= */

function iniciarUbicacion() {

    const inputUbicacion = document.getElementById(
        "ubicacion"
    );


    if (!inputUbicacion) {

        return;

    }


    const formulario = inputUbicacion.closest(
        ".formulario-chat"
    );


    if (!formulario) {

        return;

    }


    const botonUbicacion = formulario.querySelector(
        "label[for='ubicacion'], button .material-icons-rounded"
    );


    if (!botonUbicacion) {

        return;

    }


    const contenedorBoton = botonUbicacion.closest(
        "label, button"
    );


    if (!contenedorBoton) {

        return;

    }


    contenedorBoton.addEventListener(
        "click",
        function (evento) {

            evento.preventDefault();


            if (!navigator.geolocation) {

                alert(
                    "Tu navegador no permite obtener la ubicación."
                );

                return;

            }


            navigator.geolocation.getCurrentPosition(

                function (posicion) {

                    const latitud =
                        posicion.coords.latitude;

                    const longitud =
                        posicion.coords.longitude;


                    inputUbicacion.value =
                        latitud + "," + longitud;


                    alert(
                        "Ubicación agregada correctamente."
                    );

                },

                function () {

                    alert(
                        "No fue posible obtener tu ubicación."
                    );

                }

            );

        }

    );

}


/* =========================================================
   CERRAR ALERTAS AUTOMÁTICAMENTE
========================================================= */

setTimeout(function () {

    const alertas = document.querySelectorAll(
        ".alerta"
    );


    alertas.forEach(function (alerta) {

        alerta.style.transition =
            "opacity 0.3s ease";


        alerta.style.opacity = "0";


        setTimeout(function () {

            alerta.remove();

        }, 300);

    });

}, 6000);


/* =========================================================
   EVITAR DOBLE ENVÍO
========================================================= */

const formularios = document.querySelectorAll("form");


formularios.forEach(function (formulario) {

    formulario.addEventListener(
        "submit",
        function () {

            const boton = formulario.querySelector(
                "button[type='submit']"
            );


            if (!boton) {

                return;

            }


            boton.disabled = true;
            const textoOriginal =
                boton.innerHTML;


            boton.dataset.textoOriginal =
                textoOriginal;


            setTimeout(function () {

                boton.disabled = false;

                boton.innerHTML =
                    boton.dataset.textoOriginal;

            }, 2500);

        }

    );

});