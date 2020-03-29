#include <string>
#include <sstream>
#include <vector>

#include <gflags/gflags.h>
#include <glog/logging.h>
#include <glog/stl_logging.h>

DEFINE_string(confirmed,"","list of data points");
DEFINE_string(deaths,"","list of data points");
DEFINE_string(recovered,"","list of data points");

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

std::vector<int> derive(const std::vector<int>& nums) {
  std::vector<int> dn(nums.size() - 1);
  for(size_t i = 1; i < nums.size(); ++i) {
    dn[i-1] = nums[i] - nums[i-1];
  }
  return dn;
}

struct SIRCostFunctor {
  SIRCostFunctor(const int S0,
                 const int I0,
                 const int D0,
                 const T& dc,
                 const T& dd,
                 const T& dr) :
    S0_(S0),
    I0_(I0),
    D0_(D0),
    dc_(dc),
    dd_(dd),
    dr_(dr) {}
  template<typename T>
  bool operator()(const T* ki const, const T* kr const, const T* residual) {
    // SIR
    /*
    S' = -ki * S * I
    I' = ki * S * I - kr * I
    R' = kr * I
    */
    T s = -ki * 
  }
  private:
    const S0_;
    const I0_;
    const D0_;
    const T dc_;
    const T dd_;
    const T dr_;
};

int main(int argc, char** argv) {
  init(argc, argv);
  CHECK(!FLAGS_confirmed.empty()) << "Must provide confirmed";
  CHECK(!FLAGS_deaths.empty()) << "Must provide deaths";
  CHECK(!FLAGS_recovered.empty()) << "Must provide recovered";
  auto c = splitInts(FLAGS_confirmed);
  auto d = splitInts(FLAGS_deaths);
  auto r = splitInts(FLAGS_recovered);
  auto dc = derive(c);
  auto dd = derive(d);
  auto dr = derive(r);
  VLOG(2) << "Confirmed: " << c;
  VLOG(2) << "Deaths: " << d;
  VLOG(2) << "Recovered: " << r;

  VLOG(1) << "Confirmed': " << dc;
  VLOG(1) << "Deaths': " << dd;
  VLOG(1) << "Recovered': " << dr;
  return 0;
}
