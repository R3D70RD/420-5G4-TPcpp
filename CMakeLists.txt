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

# Tests C++ du coeur (recompilés séparément pour pouvoir activer les sanitizers).
option(BUILD_TESTS "Construire les tests C++ et enregistrer les tests CTest" ON)
option(ENABLE_SANITIZERS "Activer AddressSanitizer/UBSan pour les tests C++" OFF)

if(BUILD_TESTS)
    enable_testing()

    add_executable(bibliotheque_tests tests/cpp/test_core.cpp ${SOURCES})
    target_include_directories(bibliotheque_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

    if(MSVC)
        target_compile_options(bibliotheque_tests PRIVATE /W4)
    else()
        target_compile_options(bibliotheque_tests PRIVATE -Wall -Wextra -Wpedantic)
        if(ENABLE_SANITIZERS)
            target_compile_options(bibliotheque_tests PRIVATE
                -fsanitize=address,undefined -fno-omit-frame-pointer)
            target_link_options(bibliotheque_tests PRIVATE
                -fsanitize=address,undefined)
        endif()
    endif()

    if(NOT HAVE_STD_FILESYSTEM)
        target_link_libraries(bibliotheque_tests PRIVATE stdc++fs)
    endif()

    add_test(NAME cpp_core COMMAND bibliotheque_tests)
    set_tests_properties(cpp_core PROPERTIES
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
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

# Tests Python (bindings + service + smoke GUI) enregistrés dans CTest.
if(BUILD_TESTS AND TARGET bibliotheque_py)
    if(NOT Python_EXECUTABLE)
        set(Python_EXECUTABLE python3)
    endif()

    add_test(NAME python_bindings
        COMMAND ${Python_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_bindings.py)
    add_test(NAME python_service
        COMMAND ${Python_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_service.py)
    set_tests_properties(python_bindings python_service PROPERTIES
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        ENVIRONMENT "PYTHONPATH=${CMAKE_BINARY_DIR}")

    find_program(XVFB_RUN xvfb-run)
    if(XVFB_RUN)
        add_test(NAME gui_smoke
            COMMAND ${XVFB_RUN} -a ${Python_EXECUTABLE}
                    ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_gui_smoke.py)
        set_tests_properties(gui_smoke PROPERTIES
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
            ENVIRONMENT "PYTHONPATH=${CMAKE_BINARY_DIR}")
    endif()
endif()
