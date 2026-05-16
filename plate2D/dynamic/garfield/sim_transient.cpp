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

void ExportSignalComponents(Sensor& sensor, const std::string& label,
                            const std::filesystem::path& filename) {
  std::ofstream out(filename);
  if (!out) {
    std::cerr << "Could not open " << filename << " for writing.\n";
    return;
  }
  double t0 = 0., dt = 0.;
  size_t nBins = 0;
  sensor.GetTimeWindow(t0, dt, nBins);
  out << "# time_ns total_fC_per_ns prompt_fC_per_ns delayed_fC_per_ns\n";
  for (size_t i = 0; i < nBins; ++i) {
    const double t = t0 + (i + 0.5) * dt;
    out << t << ' ' << sensor.GetSignal(label, i, 0) << ' '
        << sensor.GetSignal(label, i, 1) << ' '
        << sensor.GetSignal(label, i, 2) << '\n';
  }
}

}  // namespace

int main() {
  gROOT->SetBatch(true);

  const auto activityRoot = FindActivityRoot();
  const auto meshDir = activityRoot / "output" / "mesh";
  const auto materialsFile = activityRoot / "elmer" / "materials.dat";
  const auto driftField = activityRoot / "output" / "elmer" /
                          "drift_field.result";
  const auto promptWeighting = activityRoot / "output" / "elmer" /
                               "weighting_static.result";
  const auto eqsWeighting = activityRoot / "output" / "elmer" /
                            "weighting_dynamic_eqs.result";
  const auto imageFile = activityRoot / "figures" / "signal_transient.png";
  const auto dataFile = activityRoot / "output" / "garfield" /
                        "signal_transient.dat";

  std::filesystem::create_directories(dataFile.parent_path());
  if (!std::filesystem::exists(eqsWeighting)) {
    std::cerr << "Missing EQS transient weighting map: " << eqsWeighting
              << "\nRun `ElmerSolver weighting_dynamic_eqs.sif` before "
                 "running this program.\n";
    return 1;
  }

  MediumGas gas;
  gas.SetComposition("ar", 70., "co2", 30.);
  gas.SetTemperature(293.15);
  gas.SetPressure(760.);
  // Use a fixed drift speed so the example stays lightweight and reproducible.
  gas.SetElectronVelocityE(0., 0., 0., 0.05);

  ComponentElmer2d elm;
  elm.Initialise((meshDir / "mesh.header").string(),
                 (meshDir / "mesh.elements").string(),
                 (meshDir / "mesh.nodes").string(), materialsFile.string(),
                 driftField.string(),
                 "cm");
  elm.SetMedium(1, &gas);
  elm.SetWeightingPotential(promptWeighting.string(), "Readout");
  elm.SetDynamicWeightingPotential(eqsWeighting.string(), "Readout");
  std::cout << "Using transient weighting map " << eqsWeighting << ".\n";

  Sensor sensor;
  sensor.AddComponent(&elm);
  sensor.AddElectrode(&elm, "Readout");
  sensor.EnableDelayedSignal(true);
  sensor.SetTimeWindow(0., 1.0, 1200);

  AvalancheMC drift;
  drift.SetSensor(&sensor);
  drift.SetDistanceSteps(0.001);
  // Keep this exercise deterministic: the delayed signal should come from the
  // weighting map, not from random diffusion or avalanche fluctuations.
  drift.EnableDiffusion(false);
  drift.EnableAttachment(false);
  drift.EnableMultiplication(false);

  constexpr double x0 = 10.0;
  constexpr double y0 = 1.45;
  constexpr double z0 = 0.0;
  constexpr double t0 = 0.0;

  sensor.NewSignal();
  drift.DriftElectron(x0, y0, z0, t0);
  if (drift.GetNumberOfElectronEndpoints() > 0) {
    double xi = 0., yi = 0., zi = 0., ti = 0.;
    double xf = 0., yf = 0., zf = 0., tf = 0.;
    int status = 0;
    drift.GetElectronEndpoint(0, xi, yi, zi, ti, xf, yf, zf, tf, status);
    std::cout << "Electron endpoint: (" << xf << ", " << yf << ", " << zf
              << ") cm at t = " << tf << " ns, status = " << status << ".\n";
  }

  TCanvas canvas("cSignal", "Simulated Signal", 900, 600);
  sensor.PlotSignal("Readout", &canvas);
  canvas.SaveAs(imageFile.c_str());

  ExportSignalComponents(sensor, "Readout", dataFile);
  std::cout << "Saved signal plot to " << imageFile << ".\n";
  std::cout << "Saved signal samples to " << dataFile << ".\n";
  return 0;
}
