// Gmsh Script (.geo) for Parallel Plate Capacitor with Resistive Layer
// Detector Simulation School 2026 - Static Weighting Field Activity

// --- Geometry Parameters ---
lc = 0.1;          // Characteristic mesh size
width = 20.0;      // Width of the device
gap = 1.0;         // Gas gap thickness
layer = 0.5;       // Resistive-layer thickness

// --- Points ---
Point(1) = {0, 0, 0, lc};
Point(2) = {width, 0, 0, lc};
Point(3) = {width, layer, 0, lc};
Point(4) = {0, layer, 0, lc};
Point(5) = {width, layer + gap, 0, lc};
Point(6) = {0, layer + gap, 0, lc};

// --- Lines ---
Line(1) = {1, 2};  // Bottom electrode
Line(2) = {2, 3};
Line(3) = {3, 4};  // Internal interface
Line(4) = {4, 1};
Line(5) = {3, 5};
Line(6) = {5, 6};  // Top electrode
Line(7) = {6, 4};

// --- Surfaces ---
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};  // Resistive layer

Curve Loop(2) = {5, 6, 7, -3};
Plane Surface(2) = {2};  // Gas gap

Recombine Surface {1, 2};

// --- Physical Groups ---
Physical Surface("ResistiveLayer", 1) = {1};
Physical Surface("GasGap", 2) = {2};

Physical Curve("BottomElectrode", 11) = {1};
Physical Curve("TopElectrode", 12) = {6};
