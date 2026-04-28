// Solution copy for the static weighting-field activity.

lc = 0.1;
width = 20.0;
gap = 1.0;
layer = 0.5;

Point(1) = {0, 0, 0, lc};
Point(2) = {width, 0, 0, lc};
Point(3) = {width, layer, 0, lc};
Point(4) = {0, layer, 0, lc};
Point(5) = {width, layer + gap, 0, lc};
Point(6) = {0, layer + gap, 0, lc};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Line(5) = {3, 5};
Line(6) = {5, 6};
Line(7) = {6, 4};

Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

Curve Loop(2) = {5, 6, 7, -3};
Plane Surface(2) = {2};

Recombine Surface {1, 2};

Physical Surface("ResistiveLayer", 1) = {1};
Physical Surface("GasGap", 2) = {2};

Physical Curve("BottomElectrode", 11) = {1};
Physical Curve("TopElectrode", 12) = {6};
