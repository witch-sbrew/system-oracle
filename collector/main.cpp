#define _LIBCPP_DISABLE_AVAILABILITY
#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <array>
#include <thread>
#include <chrono>
#include <libproc.h>
#include <curl/curl.h>
#include <unistd.h>
#include <format>
#include <iterator>

using namespace std::string_view_literals;

struct ProcessInfo
{
  pid_t pid;
  std::string name;
  std::string path;
  bool is_dev_tool;
};

// Determine if a path represents a development tool
bool is_development_tool(std::string_view path)
{
  // array for storage, constexpr for process at compile time
  static constexpr auto dev_indicators = std::to_array<std::string_view>({"vscode", "Code.app", "cpptools", "Terminal.app", "iterm",
                                                                          "clang", "gcc", "cmake", "ninja", "python", "node", "cargo",
                                                                          "anaconda", "miniconda", "bin/git", "bin/make"});

  return std::any_of(dev_indicators.begin(), dev_indicators.end(),
                     [path](std::string_view indicator)
                     {
                       // We use case-insensitive-like search by looking for substrings
                       return path.find(indicator) != std::string_view::npos;
                     });
}

// Get list of running processes with full paths
std::vector<ProcessInfo> get_processes()
{
  std::vector<ProcessInfo> processes;
  processes.reserve(64);

  int bytes_needed = proc_listpids(PROC_ALL_PIDS, 0, nullptr, 0); // buffer size in bytes
  if (bytes_needed <= 0)
  {
    std::cerr << "Failed to get process count\n";
    return processes;
  }

  int pid_count = bytes_needed / sizeof(pid_t);
  std::vector<pid_t> pids(pid_count);

  int bytes_returned = proc_listpids(PROC_ALL_PIDS, 0, pids.data(),
                                     static_cast<int>(pids.size() * sizeof(pid_t)));
  int actual_count = bytes_returned / sizeof(pid_t);

  for (int i = 0; i < actual_count; ++i)
  {
    if (pids[i] == 0)
      continue;

    char pathbuf[PROC_PIDPATHINFO_MAXSIZE];
    int ret = proc_pidpath(pids[i], pathbuf, sizeof(pathbuf));
    if (ret > 0)
    {
      std::string_view path_view(pathbuf);

      if (is_development_tool(path_view)) // is_development_tool(path_view)
      {
        std::cout << "Checking: " << path_view << std::endl;
        ProcessInfo info;
        info.pid = pids[i];
        info.path = std::string(path_view);
        info.is_dev_tool = is_development_tool(path_view);

        size_t last_slash = path_view.find_last_of('/');
        info.name = (last_slash != std::string_view::npos)
                        ? std::string(path_view.substr(last_slash + 1))
                        : std::string(path_view);
        processes.push_back(std::move(info));
      }
    }
  }
  return processes;
}

// Build the JSON pack without allocating hundreds of tiny temporary strings
std::string serialize_processes(const std::vector<ProcessInfo> &procs)
{
  std::string buffer;
  buffer.reserve(procs.size() * 128);

  buffer.append("{\"processes\":[");
  for (size_t i = 0; i < procs.size(); ++i)
  {
    std::format_to(std::back_inserter(buffer),
                   "{{\"pid\":{},\"name\":\"{}\",\"path\":\"{}\"}}",
                   procs[i].pid, procs[i].name, procs[i].path);

    if (i < procs.size() - 1)
      buffer.push_back(',');
  }

  buffer.append("]}");
  return buffer;
}

// Telemetry Shipper (Pack, Address, Ship)
bool ship_telemetry(const std::vector<ProcessInfo> &procs, std::string_view url)
{
  if (procs.empty())
    return true;

  // the shipper
  CURL *curl = curl_easy_init();
  if (!curl)
    return false;

  // generate pack/payload
  std::string payload = serialize_processes(procs);

  struct curl_slist *headers = nullptr;
  headers = curl_slist_append(headers, "Content-Type: application/json");

  // libcurl setup
  curl_easy_setopt(curl, CURLOPT_URL, url.data());
  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
  curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());

  // prevent stdout pollution from server responses
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, +[](void *, size_t s, size_t n, void *)
                                                { return s * n; });

  // address + send/blocking network transfer
  CURLcode res = curl_easy_perform(curl);

  curl_slist_free_all(headers);
  curl_easy_cleanup(curl);

  return res == CURLE_OK;
}

int main()
{
  std::cout << "--- System Oracle: Collector Active ---" << std::endl;
  // Collector logic goes here
  curl_global_init(CURL_GLOBAL_ALL); // for libcurl stability
  const std::string url = "http://localhost:8000/telemetry/ingest";

  int cycle = 0;
  while (true)
  {
    cycle++;
    auto processes = get_processes();
    if (!processes.empty())
    {
      std::cout << "(e.g., " << processes[0].name;
      if (processes.size() > 1)
      {
        std::cout << ", " << processes[1].name;
      }
      std::cout << ") ";
    }

    if (ship_telemetry(processes, url))
    {
      std::cout << "✓\n";
    }
    else
    {
      std::cout << "✗\n";
    }

    std::this_thread::sleep_for(std::chrono::seconds(5));
  }

  return 0;
}