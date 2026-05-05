# gdsims2026_ElmerFEM

Activities for the 2026 detector simulation school using Gmsh, Elmer, and Garfield++.

## Activity Map

- `plate2D/static`: geometry-first 2D parallel plate with a resistive layer, static weighting potential, and prompt signal readout
- `plate2D/dynamic`: the same 2D parallel plate extended to a time-dependent weighting-field exercise

## Recommended Setup

These activities assume that:

- the repository has been cloned under `/home/student`,
- `ElmerGrid` and `ElmerSolver` are installed and available in `PATH`,
- Gmsh is installed with GUI support and `gmsh` is available in `PATH`,
- Garfield++ is available at `/home/student/Software/garfield/garfield-20260325`.

If Garfield++ is somewhere else, set one of these before sourcing the setup
script:

```bash
export GARFIELD_ROOT=/path/to/garfield-20260325
```

or, if Garfield++ was installed into a separate prefix:

```bash
export GARFIELD_INSTALL=/path/to/garfield-install-prefix
```

or, if you know the exact CMake package directory:

```bash
export Garfield_DIR=/path/to/directory/containing/GarfieldConfig.cmake
```

From any activity folder, run:

```bash
source setup_env.sh
```

You can also source the setup script by absolute path, for example:

```bash
source /home/student/gdsims2026_ElmerFEM/setup_env.sh
```

The setup script checks `ElmerGrid`, `ElmerSolver`, and `gmsh`, then configures
Garfield++ for the local Garfield build/install. After that, follow the web
documentation in the activity's `docs/index.md`.

## Activity Links

- [2D Static Plate Activity](./plate2D/static/docs/index.md)
- [2D Dynamic Plate Activity](./plate2D/dynamic/docs/index.md)

Start with the static activity. It builds the geometry and introduces the
ordinary weighting potential. Then move to the dynamic activity, which reuses
the same geometry and adds the conductive relaxation of the resistive layer.
