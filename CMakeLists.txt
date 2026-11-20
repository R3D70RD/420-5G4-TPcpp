# downgrade la version minimal pour plus de comptabilité
cmake_minimum_required(VERSION 3.16) 

project(bibliotheque LANGUAGES CXX)

# Specifie qu'on veut la version C++17 du langage
set(CMAKE_CXX_STANDARD 17)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Sources du coeur metier, partagees entre l'exe console et le module Python
set(SOURCES
    book.cpp
    user.cpp
    library.cpp
    filemanager.cpp
    activitylogger.cpp
)

add_library(bibliotheque_core STATIC ${SOURCES})
target_include_directories(bibliotheque_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Indispensable pour lier cette lib statique dans le module Python (.so)
set_target_properties(bibliotheque_core PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_executable(bibliotheque main.cpp)
target_link_libraries(bibliotheque PRIVATE bibliotheque_core)

# Enable warnings
if(MSVC)
    target_compile_options(bibliotheque_core PRIVATE /W4)
else()
    target_compile_options(bibliotheque_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

# vérifie les dépendances systêmes des anciens 
include(CheckCXXSourceCompiles)
set(CMAKE_REQUIRED_FLAGS "${CMAKE_CXX_FLAGS}")
check_cxx_source_compiles("
#include <filesystem>
int main() { std::filesystem::path p{\".\"}; return p.empty(); }
" HAVE_STD_FILESYSTEM)

if(NOT HAVE_STD_FILESYSTEM)
    target_link_libraries(bibliotheque_core PUBLIC stdc++fs)
endif()

# Module Python (pybind11). Optionnel : le build console reste fonctionnel sans lui.
option(BUILD_PYTHON_BINDINGS "Construire le module Python via pybind11" ON)

if(BUILD_PYTHON_BINDINGS)
    set(PYBIND11_FINDPYTHON ON)
    find_package(pybind11 CONFIG QUIET)
    if(NOT pybind11_FOUND)
        message(WARNING
            "pybind11 introuvable : le module Python 'bibliotheque_py' ne sera pas construit. "
            "Installez-le avec : pip install pybind11")
    else()
        pybind11_add_module(bibliotheque_py bindings.cpp)
        target_link_libraries(bibliotheque_py PRIVATE bibliotheque_core)

        if(MSVC)
            target_compile_options(bibliotheque_py PRIVATE /W4)
        else()
            target_compile_options(bibliotheque_py PRIVATE -Wall -Wextra -Wpedantic)
        endif()

        # Le module doit être importable depuis build/ (PYTHONPATH=build)
        set_target_properties(bibliotheque_py PROPERTIES
            LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
            RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
    endif()
endif()