# Caja Mini-ITX tipo consola

Presentación del diseño de una caja Mini-ITX de aluminio negro anodizado, de 150 × 190 × 320 mm (≈ 9,1 L).

Se ve en GitHub Pages: <https://narfware.github.io/itx-prototype/>

Navegación: flechas del teclado, botones inferiores o deslizando en el móvil. Cada diapositiva tiene su enlace (`#1`, `#2`…).

## Modelo 3D

- Visor interactivo: <https://narfware.github.io/itx-prototype/modelo.html>
- `modelo/caja_itx.scad`: modelo paramétrico para [OpenSCAD](https://openscad.org). Cambia `part` para exportar cada pieza a STL, o `part` + `flat = true` para sacar los paneles en DXF para corte láser.
- `modelo/render.py`: el trazador de rayos (numpy) que genera `img/escritorio.jpg`.
- `modelo/piezas.py`: las mismas cotas en Python; comprueba choques entre piezas y genera `modelo/piezas.json` para el visor.

Las posiciones de los agujeros Mini-ITX y del socket están por verificar con la placa real antes de fabricar.
