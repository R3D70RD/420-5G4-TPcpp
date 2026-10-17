#include <ctime>
#include <filesystem>
#include <fstream>

#include "activitylogger.h"
#include "filemanager.h"

using namespace std;

// Crée le dossier logs/ à la racine du projet si nécessaire
ActivityLogger::ActivityLogger() {
    filesystem::path dir = filesystem::path(getProjectRoot()) / "logs";
    try {
        filesystem::create_directories(dir);
    } catch (const filesystem::filesystem_error&) { }
    logFilePath = (dir / "activity.log").string();
}

void ActivityLogger::log(const string& action, const string& details) {
    ofstream file(logFilePath, ios::app); // l'historique est conservé entre les sessions
    if (!file.is_open()) return;

    time_t now = time(nullptr);
    char buffer[32];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", localtime(&now));

    file << buffer << " - [" << action << "]";
    if (!details.empty()) file << " " << details;
    file << "\n";
}

vector<string> ActivityLogger::getLastEntries(size_t count) const {
    vector<string> lines;
    ifstream file(logFilePath);
    string line;
    while (getline(file, line)) {
        if (!line.empty()) lines.push_back(line);
    }
    if (lines.size() > count) {
        lines.erase(lines.begin(), lines.end() - count);
    }
    return lines;
}

string ActivityLogger::getLogFilePath() const { return logFilePath; }