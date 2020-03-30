#include <string>
#include <sstream>
#include <iostream>
#include <vector>

#include <gflags/gflags.h>
#include <glog/logging.h>
#include <glog/stl_logging.h>
#include <Eigen/Core>
#include <ceres/ceres.h>

DEFINE_string(confirmed,"","list of data points");
DEFINE_string(deaths,"","list of data points");
DEFINE_string(recovered,"","list of data points");
DEFINE_uint64(population,1e9,"population");
DEFINE_int32(trim,0, "days to trim from front");

void init(int& argc, char** argv) {
  ::google::ParseCommandLineFlags(&argc, &argv, false);
  ::google::InitGoogleLogging(argv[0]);
  ::google::InstallFailureSignalHandler();
}

std::vector<int> splitInts(const std::string& data, char delim=',') {
  std::vector<int> output;
  std::stringstream ss;
  for (const auto& c : data) {
    if (c == delim) {
      output.emplace_back(::atoi(ss.str().c_str()));
      ss.str(std::string());
    } else {
      ss << c;
    }
  }
  if(!ss.str().empty()) {
    output.emplace_back(::atoi(ss.str().c_str()));
  }
  return output;
}

std::string toJson(int pop, double ki, double kr, int i0 = 1, int r0 = 2) {
  std::stringstream ss;
  ss << "{\"population\":" << pop <<",\"ki\":"<<ki<<",\"kr\":"<<kr<<",\"i0\":"<<i0<<",\"r0\":"<<r0<<"}";
  return ss.str();
}

std::vector<int> derive(const std::vector<int>& nums) {
  std::vector<int> dn(nums.size() - 1);
  for(size_t i = 1; i < nums.size(); ++i) {
    dn[i-1] = nums[i] - nums[i-1];
  }
  return dn;
}

struct SIRCostFunctor {
  SIRCostFunctor(const double& i,
                 const double& r,
                 const double& ds,
                 const double& di,
                 const double& dr) :
    i_(i),
    r_(r),
    ds_(ds),
    di_(di),
    dr_(dr) {}
  template<typename T>
  bool operator()(const T* const s0, const T* const ki, const T* const kr, T* residuals) const {
    // SIR
    /*
    S' = -ki * S * I
    I' = ki * S * I - kr * I
    R' = kr * I
    */
    T s = T(*s0) - i_ - r_;
    T s_p = -T(*ki) * T(s) * T(i_);
    T i_p = T(*ki) * T(s) * T(i_) - T(*kr) * T(i_);
    T r_p = T(*kr) * T(i_);

    residuals[0] = s_p - T(ds_);
    residuals[1] = i_p - T(di_);
    residuals[2] = r_p - T(dr_);
    return true;
  }
  private:
    const double i_;
    const double r_;
    const double ds_;
    const double di_;
    const double dr_;
};

void stripToFirstCase(std::vector<int>& cases) {
  while(cases.front() == 0) {
    cases.erase(cases.begin());
  }
}

void stripToSize(std::vector<int>& cases, size_t size) {
  while(cases.size() > size) {
    cases.erase(cases.begin());
  }
}

bool runOptimization(
    const std::vector<int>& confirmed,
    const std::vector<int>& deaths,
    const std::vector<int>& recovered,
    const std::vector<int>& d_conf,
    const std::vector<int>& d_deaths,
    const std::vector<int>& d_recovered,
    double* s0,
    double* ki,
    double* kr) {
  ceres::Problem problem;
  for (size_t j = 0; j < d_conf.size(); ++j) {
    double dr = d_recovered[j] + d_deaths[j];
    double di = d_conf[j] - dr;
    double ds = -d_conf[j];
    double removed = deaths[j+1] + recovered[j+1];
    double infected = confirmed[j+1] - removed;
    problem.AddResidualBlock(
        new ceres::AutoDiffCostFunction<SIRCostFunctor, 3, 1, 1, 1>(new SIRCostFunctor(infected, removed,ds,di,dr)), nullptr, s0, ki, kr);
  }
  problem.SetParameterLowerBound(s0,0,0);
  problem.SetParameterLowerBound(ki,0,0);
  problem.SetParameterLowerBound(kr,0,0);
  ceres::Solver::Summary summary;
  ceres::Solver::Options opts;
  opts.max_num_iterations = 1000;
  opts.num_threads = 4;
  ceres::Solve(opts, &problem, &summary);
  VLOG(2) << summary.FullReport();
  return summary.IsSolutionUsable();
}

int main(int argc, char** argv) {
  init(argc, argv);
  CHECK(!FLAGS_confirmed.empty()) << "Must provide confirmed";
  CHECK(!FLAGS_deaths.empty()) << "Must provide deaths";
  CHECK(!FLAGS_recovered.empty()) << "Must provide recovered";
  auto c = splitInts(FLAGS_confirmed);
  auto d = splitInts(FLAGS_deaths);
  auto r = splitInts(FLAGS_recovered);
  stripToSize(c,c.size() - FLAGS_trim);
  stripToSize(d,c.size());
  stripToSize(r,c.size());
  auto dc = derive(c);
  auto dd = derive(d);
  auto dr = derive(r);
  VLOG(2) << "Confirmed: " << c;
  VLOG(2) << "Deaths: " << d;
  VLOG(2) << "Recovered: " << r;

  VLOG(1) << "Confirmed': " << dc;
  VLOG(1) << "Deaths': " << dd;
  VLOG(1) << "Recovered': " << dr;
  double ki = 0.1;
  double kr = 0.1;
  double s0 = FLAGS_population;
  int r0 = d[0]+r[0];
  int i0 = c[0]-r[0];
  runOptimization(c,d,r,dc,dd,dr,&s0,&ki,&kr);
  std::cout << toJson(s0,ki,kr,i0,r0) << std::endl;
  return 0;
}
