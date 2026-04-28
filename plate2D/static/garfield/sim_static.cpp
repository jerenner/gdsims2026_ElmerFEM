#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include <TCanvas.h>
#include <TROOT.h>

#include "Garfield/AvalancheMC.hh"
#include "Garfield/ComponentElmer2d.hh"
#include "Garfield/MediumGas.hh"
#include "Garfield/Sensor.hh"

using namespace Garfield;

namespace {

std::filesystem::path FindActivityRoot() {
  auto path = std::filesystem::current_path();
  for (size_t i = 0; i < 5; ++i) {
    if (std::filesystem::exists(path / "geometry" / "ppc_geometry.geo") &&
        std::filesystem::exists(path / "output" / "mesh" / "mesh.header")) {
      return path;
    }
    if (!path.has_parent_path()) break;
    path = path.parent_path();
  }
  return std::filesystem::current_path();
}

void ExportSignal(Sensor& sensor, const std::string& label,
                  const std::filesystem::path& filename) {
  std::ofstream out(filename);
  if (!out) {
    std::cerr << "Could not open " << filename << " for writing.\n";
    return;
  }
  double t0 = 0., dt = 0.;
  size_t nBins = 0;
  sensor.GetTimeWindow(t0, dt, nBins);
  out << "# time_ns total_fC_per_ns\n";
  for (size_t i = 0; i < nBins; ++i) {
    const double t = t0 + (i + 0.5) * dt;
    out << t << ' ' << sensor.GetSignal(label, i, 0) << '\n';
  }
}

}  // namespace

int main() {
  gROOT->SetBatch(true);

  const auto activityRoot = FindActivityRoot();
  const auto meshDir = activityRoot / "output" / "mesh";
  const auto materialsFile = activityRoot / "elmer" / "materials.dat";
  const auto electricField = activityRoot / "output" / "elmer" /
                             "electric_field.result";
  const auto weightingField = activityRoot / "output" / "elmer" /
                              "weighting_field.result";
  const auto imageFile = activityRoot / "figures" / "signal_static.png";
  const auto dataFile = activityRoot / "output" / "garfield" /
                        "signal_static.dat";

  std::filesystem::create_directories(imageFile.parent_path());
  std::filesystem::create_directories(dataFile.parent_path());

  MediumGas gas;
  gas.SetComposition("ar", 70., "co2", 30.);
  gas.SetTemperature(293.15);
  gas.SetPressure(760.);
  // Fixed transport makes the activity lightweight and reproducible.
  gas.SetElectronVelocityE(0., 0., 0., 0.05);

  ComponentElmer2d elm;
  elm.Initialise((meshDir / "mesh.header").string(),
                 (meshDir / "mesh.elements").string(),
                 (meshDir / "mesh.nodes").string(),
                 materialsFile.string(),
                 electricField.string(), "cm");
  elm.SetMedium(1, &gas);
  elm.SetWeightingPotential(weightingField.string(), "Readout");

  Sensor sensor;
  sensor.AddComponent(&elm);
  sensor.AddElectrode(&elm, "Readout");
  sensor.SetTimeWindow(0., 0.1, 400);

  AvalancheMC drift;
  drift.SetSensor(&sensor);
  drift.SetDistanceSteps(0.001);
  // Keep the prompt-signal check deterministic for the tutorial.
  drift.EnableDiffusion(false);
  drift.EnableAttachment(false);
  drift.EnableMultiplication(false);

  constexpr double x0 = 10.0;
  constexpr double y0 = 1.45;
  constexpr double z0 = 0.0;
  constexpr double t0 = 0.0;

  sensor.NewSignal();
  drift.DriftElectron(x0, y0, z0, t0);

  TCanvas canvas("cSignal", "Static Weighting-Field Signal", 900, 600);
  sensor.PlotSignal("Readout", &canvas);
  canvas.SaveAs(imageFile.c_str());

  ExportSignal(sensor, "Readout", dataFile);
  std::cout << "Saved signal plot to " << imageFile << ".\n";
  std::cout << "Saved signal samples to " << dataFile << ".\n";
  return 0;
}
