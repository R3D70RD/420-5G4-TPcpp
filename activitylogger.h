#ifndef ACTIVITYLOGGER_H
#define ACTIVITYLOGGER_H

#include <string>
#include <vector>

using namespace std;

class ActivityLogger {
private:
    string logFilePath;

public:
    ActivityLogger();

    // format : "AAAA-MM-JJ HH:MM:SS | ACTION | détails"
    void log(const string& action, const string& details = "");

    // Retourne les dernières entrées du journal
    vector<string> getLastEntries(size_t count) const;

    string getLogFilePath() const;
};

#endif