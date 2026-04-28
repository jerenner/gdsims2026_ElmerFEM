# gdsims2026_ElmerFEM

Activities for the 2026 detector simulation school using Gmsh, Elmer, and Garfield++.

## Activity Map

- `plate2D/static`: geometry-first 2D parallel plate with a resistive layer, static weighting potential, and prompt signal readout
- `plate2D/dynamic`: the same 2D parallel plate extended to a time-dependent weighting-field exercise

## Recommended Setup

These activities assume that:

- `garfieldpp`, `elmerfem`, and `gmsh` are already available next to this repository,
- Garfield++ has already been built and installed at `../garfieldpp/install`,
- Elmer has already been built at `../elmerfem/build`,
- Gmsh has already been built at `../gmsh/build`.

From any activity folder, run:

```bash
source setup_env.sh
```

and then follow the web documentation in that activity's `docs/index.md`.

## Activity Links

- [2D Static Plate Activity](./plate2D/static/docs/index.md)
- [2D Dynamic Plate Activity](./plate2D/dynamic/docs/index.md)

Start with the static activity. It builds the geometry and introduces the
ordinary weighting potential. Then move to the dynamic activity, which reuses
the same geometry and adds the conductive relaxation of the resistive layer.
