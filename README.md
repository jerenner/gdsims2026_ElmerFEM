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
- Python 3 and Matplotlib are installed,
- Garfield++ is available at `/home/student/Software/garfield/garfield-20260325`,
- the student's shell startup file sources Garfield++ setup, for example
  `/home/student/Software/garfield/garfield-20260325/build/setupGarfield.sh`.

The repository setup script is only a sanity check. It does not try to build or
discover the full software stack. If Garfield++ is somewhere else, set
`GARFIELD_ROOT` before sourcing the setup script:

```bash
export GARFIELD_ROOT=/path/to/garfield-20260325
```

If you know the exact CMake package directory, you can set this instead:

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

The setup script checks `ElmerGrid`, `ElmerSolver`, `gmsh`, `cmake`, `python3`,
Matplotlib, and the Garfield++ CMake environment. If Garfield++ was not already
configured, it tries to source the default Garfield++ setup script. After that,
follow the web documentation in the activity's `docs/index.md`.

## Activity Links

- [2D Static Plate Activity](./plate2D/static/docs/index.md)
- [2D Dynamic Plate Activity](./plate2D/dynamic/docs/index.md)

Start with the static activity. It builds the geometry and introduces the
ordinary weighting potential. Then move to the dynamic activity, which reuses
the same geometry and adds the conductive relaxation of the resistive layer.
