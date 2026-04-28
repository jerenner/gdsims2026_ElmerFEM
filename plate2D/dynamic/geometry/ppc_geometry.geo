// Gmsh Script (.geo) for Parallel Plate Capacitor with Resistive Layer
// School Year 2026 - Detector Simulation School

// --- Geometry Parameters ---
lc = 0.1;           // Characteristic length (mesh size)
width = 20.0;      // Width of plates
gap = 1.0;         // Gas gap thickness
layer = 0.5;       // Resistive layer thickness

// --- Points (x, y, z, lc) ---
// Bottom Layer
Point(1) = {0, 0, 0, lc};
Point(2) = {width, 0, 0, lc};
Point(3) = {width, layer, 0, lc};
Point(4) = {0, layer, 0, lc};

// Top Layer
Point(5) = {width, layer + gap, 0, lc};
Point(6) = {0, layer + gap, 0, lc};

// --- Lines ---
Line(1) = {1, 2}; // Bottom Electrode
Line(2) = {2, 3};
Line(3) = {3, 4}; // Interface (Internal)
Line(4) = {4, 1};

Line(5) = {3, 5};
Line(6) = {5, 6}; // Top Electrode
Line(7) = {6, 4};

// --- Surfaces ---
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1}; // Resistive Plate

Curve Loop(2) = {5, 6, 7, -3};
Plane Surface(2) = {2}; // Gas Gap

Recombine Surface {1, 2};

// --- Physical Groups (Used by Elmer to assign properties) ---
Physical Surface("ResistiveLayer", 1) = {1};
Physical Surface("GasGap", 2) = {2};

Physical Curve("BottomElectrode", 11) = {1};
Physical Curve("TopElectrode", 12) = {6};
